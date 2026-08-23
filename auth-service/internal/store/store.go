// Package store defines the persistence interface for the auth service.
package store

import (
	"errors"
	"time"
)

// Sentinel errors.
var (
	ErrNotFound      = errors.New("not found")
	ErrDuplicate     = errors.New("duplicate")
	ErrExpired       = errors.New("expired")
	ErrRevoked       = errors.New("revoked")
)

// User represents a registered human user.
type User struct {
	ID           string // canonical UUID string
	Email        string
	PasswordHash string // argon2id encoded hash
	FirstName    string
	LastName     string
	CreatedAt    time.Time
}

// RefreshToken represents a stored (hashed) refresh token.
type RefreshToken struct {
	TokenHash string    // SHA-256 of the raw token, hex-encoded
	UserID    string    // associated user UUID
	ExpiresAt time.Time
	Revoked   bool
}

// MachineClient represents an OAuth2 machine client (for Part B).
type MachineClient struct {
	ClientID     string
	SecretHash   string // argon2id hash of the secret
	Audience     string
	Scopes       string // space-delimited
	CreatedAt    time.Time
}

// Store is the persistence interface for the auth service.
// The in-memory implementation is used in tests; PostgreSQL is used in production.
type Store interface {
	// Users
	CreateUser(u User) error
	GetUserByEmail(email string) (User, error)
	GetUserByID(id string) (User, error)
	DeleteUser(id string) error

	// Refresh tokens
	CreateRefreshToken(t RefreshToken) error
	GetRefreshToken(tokenHash string) (RefreshToken, error)
	// RotateRefreshToken looks up oldHash, marks it revoked, stores the new token.
	// Returns ErrNotFound if oldHash doesn't exist, ErrRevoked if already revoked,
	// ErrExpired if past expiry.
	RotateRefreshToken(oldHash string, newToken RefreshToken) error
	// RevokeRefreshToken marks a token as revoked without issuing a replacement.
	RevokeRefreshToken(tokenHash string) error

	// Machine clients (storage foundation for Part B)
	CreateMachineClient(c MachineClient) error
	GetMachineClientByID(clientID string) (MachineClient, error)
}
