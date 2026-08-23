package store

import (
	"database/sql"
	_ "embed"
	"errors"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

//go:embed migrations/001_init.sql
var initSQL string

type PostgresStore struct {
	db *sql.DB
}

func NewPostgresStore(dsn string) (*PostgresStore, error) {
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("open postgres: %w", err)
	}
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("ping postgres: %w", err)
	}
	return &PostgresStore{db: db}, nil
}

func (p *PostgresStore) Migrate() error {
	_, err := p.db.Exec(initSQL)
	return err
}

func (p *PostgresStore) Close() error {
	return p.db.Close()
}

func (p *PostgresStore) CreateUser(u User) error {
	_, err := p.db.Exec(
		`INSERT INTO users (id, email, password_hash, first_name, last_name, created_at)
		 VALUES ($1, $2, $3, $4, $5, $6)`,
		u.ID, u.Email, u.PasswordHash, u.FirstName, u.LastName, u.CreatedAt,
	)
	if err != nil {
		if isDuplicateError(err) {
			return ErrDuplicate
		}
		return fmt.Errorf("insert user: %w", err)
	}
	return nil
}

func (p *PostgresStore) GetUserByEmail(email string) (User, error) {
	var u User
	err := p.db.QueryRow(
		`SELECT id, email, password_hash, first_name, last_name, created_at FROM users WHERE email = $1`,
		email,
	).Scan(&u.ID, &u.Email, &u.PasswordHash, &u.FirstName, &u.LastName, &u.CreatedAt)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return User{}, ErrNotFound
		}
		return User{}, fmt.Errorf("get user by email: %w", err)
	}
	return u, nil
}

func (p *PostgresStore) GetUserByID(id string) (User, error) {
	var u User
	err := p.db.QueryRow(
		`SELECT id, email, password_hash, first_name, last_name, created_at FROM users WHERE id = $1`,
		id,
	).Scan(&u.ID, &u.Email, &u.PasswordHash, &u.FirstName, &u.LastName, &u.CreatedAt)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return User{}, ErrNotFound
		}
		return User{}, fmt.Errorf("get user by id: %w", err)
	}
	return u, nil
}

func (p *PostgresStore) DeleteUser(id string) error {
	res, err := p.db.Exec(`DELETE FROM users WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete user: %w", err)
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

func (p *PostgresStore) CreateRefreshToken(t RefreshToken) error {
	_, err := p.db.Exec(
		`INSERT INTO refresh_tokens (token_hash, user_id, expires_at, revoked) VALUES ($1, $2, $3, $4)`,
		t.TokenHash, t.UserID, t.ExpiresAt, t.Revoked,
	)
	if err != nil {
		return fmt.Errorf("insert refresh token: %w", err)
	}
	return nil
}

func (p *PostgresStore) GetRefreshToken(tokenHash string) (RefreshToken, error) {
	var t RefreshToken
	err := p.db.QueryRow(
		`SELECT token_hash, user_id, expires_at, revoked FROM refresh_tokens WHERE token_hash = $1`,
		tokenHash,
	).Scan(&t.TokenHash, &t.UserID, &t.ExpiresAt, &t.Revoked)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return RefreshToken{}, ErrNotFound
		}
		return RefreshToken{}, fmt.Errorf("get refresh token: %w", err)
	}
	return t, nil
}

func (p *PostgresStore) RotateRefreshToken(oldHash string, newToken RefreshToken) error {
	tx, err := p.db.Begin()
	if err != nil {
		return fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback()

	var revoked bool
	var expiresAt time.Time
	err = tx.QueryRow(
		`SELECT revoked, expires_at FROM refresh_tokens WHERE token_hash = $1`,
		oldHash,
	).Scan(&revoked, &expiresAt)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return ErrNotFound
		}
		return fmt.Errorf("lookup refresh token: %w", err)
	}
	if revoked {
		return ErrRevoked
	}
	if time.Now().UTC().After(expiresAt) {
		return ErrExpired
	}

	if _, err := tx.Exec(`UPDATE refresh_tokens SET revoked = TRUE WHERE token_hash = $1`, oldHash); err != nil {
		return fmt.Errorf("revoke old token: %w", err)
	}

	if _, err := tx.Exec(
		`INSERT INTO refresh_tokens (token_hash, user_id, expires_at, revoked) VALUES ($1, $2, $3, $4)`,
		newToken.TokenHash, newToken.UserID, newToken.ExpiresAt, newToken.Revoked,
	); err != nil {
		return fmt.Errorf("insert new token: %w", err)
	}

	return tx.Commit()
}

func (p *PostgresStore) RevokeRefreshToken(tokenHash string) error {
	res, err := p.db.Exec(`UPDATE refresh_tokens SET revoked = TRUE WHERE token_hash = $1`, tokenHash)
	if err != nil {
		return fmt.Errorf("revoke refresh token: %w", err)
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

func (p *PostgresStore) CreateMachineClient(c MachineClient) error {
	_, err := p.db.Exec(
		`INSERT INTO machine_clients (client_id, secret_hash, audience, scopes, created_at) VALUES ($1, $2, $3, $4, $5)`,
		c.ClientID, c.SecretHash, c.Audience, c.Scopes, c.CreatedAt,
	)
	if err != nil {
		if isDuplicateError(err) {
			return ErrDuplicate
		}
		return fmt.Errorf("insert machine client: %w", err)
	}
	return nil
}

func (p *PostgresStore) GetMachineClientByID(clientID string) (MachineClient, error) {
	var c MachineClient
	err := p.db.QueryRow(
		`SELECT client_id, secret_hash, audience, scopes, created_at FROM machine_clients WHERE client_id = $1`,
		clientID,
	).Scan(&c.ClientID, &c.SecretHash, &c.Audience, &c.Scopes, &c.CreatedAt)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return MachineClient{}, ErrNotFound
		}
		return MachineClient{}, fmt.Errorf("get machine client: %w", err)
	}
	return c, nil
}

func isDuplicateError(err error) bool {
	if err == nil {
		return false
	}
	return contains(err.Error(), "duplicate key") || contains(err.Error(), "unique constraint")
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 ||
		func() bool {
			for i := 0; i <= len(s)-len(substr); i++ {
				if s[i:i+len(substr)] == substr {
					return true
				}
			}
			return false
		}())
}
