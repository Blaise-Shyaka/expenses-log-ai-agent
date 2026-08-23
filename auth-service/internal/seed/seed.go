package seed

import (
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"time"

	"golang.org/x/crypto/argon2"

	"github.com/blaise/momo-expenses/auth-service/internal/store"
)

type MachineClientConfig struct {
	ClientID string
	Secret   string
	Audience string
	Scopes   string
}

func MachineClients(st store.Store, clients []MachineClientConfig) error {
	for _, cfg := range clients {
		if cfg.Secret == "" {
			return fmt.Errorf("secret for client %q is empty", cfg.ClientID)
		}
		hash, err := hashSecret(cfg.Secret)
		if err != nil {
			return fmt.Errorf("hash secret for %q: %w", cfg.ClientID, err)
		}
		err = st.CreateMachineClient(store.MachineClient{
			ClientID:  cfg.ClientID,
			SecretHash: hash,
			Audience:  cfg.Audience,
			Scopes:    cfg.Scopes,
			CreatedAt: time.Now().UTC(),
		})
		if err != nil && !errors.Is(err, store.ErrDuplicate) {
			return fmt.Errorf("create machine client %q: %w", cfg.ClientID, err)
		}
	}
	return nil
}

func DevUser(st store.Store, userID, email, password string) error {
	hash, err := hashSecret(password)
	if err != nil {
		return fmt.Errorf("hash dev user password: %w", err)
	}
	err = st.CreateUser(store.User{
		ID:           userID,
		Email:        email,
		PasswordHash: hash,
		FirstName:    "Dev",
		LastName:     "User",
		CreatedAt:    time.Now().UTC(),
	})
	if err != nil && !errors.Is(err, store.ErrDuplicate) {
		return fmt.Errorf("create dev user: %w", err)
	}
	return nil
}

func hashSecret(secret string) (string, error) {
	salt := make([]byte, 16)
	if _, err := rand.Read(salt); err != nil {
		return "", fmt.Errorf("generate salt: %w", err)
	}
	const (
		timeCost = 1
		memory   = 64 * 1024
		threads  = 4
		keyLen   = 32
	)
	hash := argon2.IDKey([]byte(secret), salt, timeCost, memory, threads, keyLen)
	encoded := fmt.Sprintf("$argon2id$v=%d$m=%d,t=%d,p=%d$%s$%s",
		argon2.Version,
		memory,
		timeCost,
		threads,
		base64.RawStdEncoding.EncodeToString(salt),
		base64.RawStdEncoding.EncodeToString(hash),
	)
	return encoded, nil
}
