package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"github.com/blaise/momo-expenses/auth-service/internal/store"
	"github.com/blaise/momo-expenses/auth-service/internal/tokens"
)

type tokenResponse struct {
	AccessToken  string `json:"access_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	RefreshToken string `json:"refresh_token,omitempty"`
}

func Token(st store.Store, minter *tokens.Minter) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if err := r.ParseForm(); err != nil {
			writeTokenError(w, http.StatusBadRequest, "invalid_request", "cannot parse form body")
			return
		}

		switch r.FormValue("grant_type") {
		case "client_credentials":
			handleClientCredentials(w, r, st, minter)
		case "refresh_token":
			handleRefreshToken(w, r, st, minter)
		case "":
			writeTokenError(w, http.StatusBadRequest, "invalid_request", "grant_type is required")
		default:
			writeTokenError(w, http.StatusBadRequest, "unsupported_grant_type", "grant_type not supported")
		}
	}
}

func handleClientCredentials(w http.ResponseWriter, r *http.Request, st store.Store, minter *tokens.Minter) {
	clientID, clientSecret, ok := r.BasicAuth()
	if !ok || clientID == "" {
		clientID = r.FormValue("client_id")
		clientSecret = r.FormValue("client_secret")
	}
	if clientID == "" || clientSecret == "" {
		writeTokenError(w, http.StatusUnauthorized, "invalid_client", "client_id and client_secret required")
		return
	}

	client, err := st.GetMachineClientByID(clientID)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			writeTokenError(w, http.StatusUnauthorized, "invalid_client", "invalid credentials")
			return
		}
		writeTokenError(w, http.StatusInternalServerError, "server_error", "internal error")
		return
	}

	valid, err := verifyArgon2id(clientSecret, client.SecretHash)
	if err != nil || !valid {
		writeTokenError(w, http.StatusUnauthorized, "invalid_client", "invalid credentials")
		return
	}

	const ttl = 15 * time.Minute
	accessToken, err := minter.MintServiceToken(client.ClientID, client.Audience, client.Scopes, ttl)
	if err != nil {
		writeTokenError(w, http.StatusInternalServerError, "server_error", "internal error")
		return
	}

	writeJSON(w, http.StatusOK, tokenResponse{
		AccessToken: accessToken,
		TokenType:   "Bearer",
		ExpiresIn:   int(ttl.Seconds()),
	})
}

func handleRefreshToken(w http.ResponseWriter, r *http.Request, st store.Store, minter *tokens.Minter) {
	rawToken := r.FormValue("refresh_token")
	if rawToken == "" {
		writeTokenError(w, http.StatusBadRequest, "invalid_request", "refresh_token is required")
		return
	}

	oldHash := tokens.HashRefreshToken(rawToken)

	existing, err := st.GetRefreshToken(oldHash)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			writeTokenError(w, http.StatusUnauthorized, "invalid_grant", "invalid refresh token")
			return
		}
		writeTokenError(w, http.StatusInternalServerError, "server_error", "internal error")
		return
	}

	rawNew, hashNew, err := tokens.GenerateRefreshToken()
	if err != nil {
		writeTokenError(w, http.StatusInternalServerError, "server_error", "internal error")
		return
	}

	newRT := store.RefreshToken{
		TokenHash: hashNew,
		UserID:    existing.UserID,
		ExpiresAt: time.Now().UTC().Add(refreshTokenTTL),
	}

	if err := st.RotateRefreshToken(oldHash, newRT); err != nil {
		switch {
		case errors.Is(err, store.ErrRevoked), errors.Is(err, store.ErrExpired):
			writeTokenError(w, http.StatusUnauthorized, "invalid_grant", "refresh token is invalid or expired")
		default:
			writeTokenError(w, http.StatusInternalServerError, "server_error", "internal error")
		}
		return
	}

	accessToken, err := minter.MintUserToken(existing.UserID, accessTokenTTL)
	if err != nil {
		writeTokenError(w, http.StatusInternalServerError, "server_error", "internal error")
		return
	}

	writeJSON(w, http.StatusOK, tokenResponse{
		AccessToken:  accessToken,
		TokenType:    "Bearer",
		ExpiresIn:    int(accessTokenTTL.Seconds()),
		RefreshToken: rawNew,
	})
}

func writeTokenError(w http.ResponseWriter, status int, code, description string) {
	writeJSON(w, status, map[string]string{"error": code, "error_description": description})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v)
}
