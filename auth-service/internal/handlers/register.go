package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"golang.org/x/crypto/argon2"
	"crypto/rand"
	"encoding/base64"
	"fmt"

	"github.com/google/uuid"

	"github.com/blaise/momo-expenses/auth-service/internal/store"
)

type RegisterRequest struct {
	Email     string `json:"email"`
	Password  string `json:"password"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
}

type RegisterResponse struct {
	ID    string `json:"id"`
	Email string `json:"email"`
}

func hashPasswordArgon2id(password string) (string, error) {
	salt := make([]byte, 16)
	if _, err := rand.Read(salt); err != nil {
		return "", fmt.Errorf("generate salt: %w", err)
	}
	const (
		time_   = 1
		memory  = 64 * 1024
		threads = 4
		keyLen  = 32
	)
	hash := argon2.IDKey([]byte(password), salt, time_, memory, threads, keyLen)
	encoded := fmt.Sprintf("$argon2id$v=%d$m=%d,t=%d,p=%d$%s$%s",
		argon2.Version,
		memory,
		time_,
		threads,
		base64.RawStdEncoding.EncodeToString(salt),
		base64.RawStdEncoding.EncodeToString(hash),
	)
	return encoded, nil
}

func Register(st store.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var req RegisterRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
			return
		}
		if req.Email == "" || req.Password == "" || req.FirstName == "" || req.LastName == "" {
			http.Error(w, `{"error":"missing required fields"}`, http.StatusBadRequest)
			return
		}

		hash, err := hashPasswordArgon2id(req.Password)
		if err != nil {
			http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
			return
		}

		u := store.User{
			ID:           uuid.New().String(),
			Email:        req.Email,
			PasswordHash: hash,
			FirstName:    req.FirstName,
			LastName:     req.LastName,
			CreatedAt:    time.Now().UTC(),
		}
		if err := st.CreateUser(u); err != nil {
			if errors.Is(err, store.ErrDuplicate) {
				w.Header().Set("Content-Type", "application/json")
				w.WriteHeader(http.StatusConflict)
				json.NewEncoder(w).Encode(map[string]string{"error": "email already registered"})
				return
			}
			http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(RegisterResponse{ID: u.ID, Email: u.Email})
	}
}
