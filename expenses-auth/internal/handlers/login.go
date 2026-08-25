package handlers

import (
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"time"

	"golang.org/x/crypto/argon2"

	"github.com/blaise/momo-expenses/expenses-auth/internal/store"
	"github.com/blaise/momo-expenses/expenses-auth/internal/tokens"
)

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type LoginResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
}

const accessTokenTTL = 15 * time.Minute
const refreshTokenTTL = 30 * 24 * time.Hour

func verifyArgon2id(password, encoded string) (bool, error) {
	parts := strings.Split(encoded, "$")
	if len(parts) != 6 {
		return false, fmt.Errorf("invalid hash format")
	}

	var version int
	if _, err := fmt.Sscanf(parts[2], "v=%d", &version); err != nil {
		return false, fmt.Errorf("parse version: %w", err)
	}

	var memory, timeCost, threads uint32
	if _, err := fmt.Sscanf(parts[3], "m=%d,t=%d,p=%d", &memory, &timeCost, &threads); err != nil {
		return false, fmt.Errorf("parse params: %w", err)
	}

	salt, err := base64.RawStdEncoding.DecodeString(parts[4])
	if err != nil {
		return false, fmt.Errorf("decode salt: %w", err)
	}

	expectedHash, err := base64.RawStdEncoding.DecodeString(parts[5])
	if err != nil {
		return false, fmt.Errorf("decode hash: %w", err)
	}

	computed := argon2.IDKey([]byte(password), salt, timeCost, memory, uint8(threads), uint32(len(expectedHash)))
	return subtle.ConstantTimeCompare(computed, expectedHash) == 1, nil
}

func Login(st store.Store, minter *tokens.Minter) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req LoginRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
			return
		}

		writeUnauthorized := func() {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusUnauthorized)
			json.NewEncoder(w).Encode(map[string]string{"error": "invalid credentials"})
		}

		u, err := st.GetUserByEmail(req.Email)
		if err != nil {
			if errors.Is(err, store.ErrNotFound) {
				writeUnauthorized()
				return
			}
			http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
			return
		}

		ok, err := verifyArgon2id(req.Password, u.PasswordHash)
		if err != nil || !ok {
			writeUnauthorized()
			return
		}

		accessToken, err := minter.MintUserToken(u.ID, accessTokenTTL)
		if err != nil {
			http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
			return
		}

		rawRefresh, hashRefresh, err := tokens.GenerateRefreshToken()
		if err != nil {
			http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
			return
		}

		rt := store.RefreshToken{
			TokenHash: hashRefresh,
			UserID:    u.ID,
			ExpiresAt: time.Now().UTC().Add(refreshTokenTTL),
		}
		if err := st.CreateRefreshToken(rt); err != nil {
			http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(LoginResponse{
			AccessToken:  accessToken,
			RefreshToken: rawRefresh,
			ExpiresIn:    int(accessTokenTTL.Seconds()),
		})
	}
}
