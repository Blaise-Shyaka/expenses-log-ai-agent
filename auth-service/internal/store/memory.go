package store

import (
	"sync"
	"time"
)

type MemoryStore struct {
	mu             sync.RWMutex
	users          map[string]User
	usersByEmail   map[string]string
	refreshTokens  map[string]RefreshToken
	machineClients map[string]MachineClient
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{
		users:          make(map[string]User),
		usersByEmail:   make(map[string]string),
		refreshTokens:  make(map[string]RefreshToken),
		machineClients: make(map[string]MachineClient),
	}
}

func (m *MemoryStore) CreateUser(u User) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if _, exists := m.usersByEmail[u.Email]; exists {
		return ErrDuplicate
	}
	if u.CreatedAt.IsZero() {
		u.CreatedAt = time.Now().UTC()
	}
	m.users[u.ID] = u
	m.usersByEmail[u.Email] = u.ID
	return nil
}

func (m *MemoryStore) GetUserByEmail(email string) (User, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	id, ok := m.usersByEmail[email]
	if !ok {
		return User{}, ErrNotFound
	}
	return m.users[id], nil
}

func (m *MemoryStore) GetUserByID(id string) (User, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	u, ok := m.users[id]
	if !ok {
		return User{}, ErrNotFound
	}
	return u, nil
}

func (m *MemoryStore) DeleteUser(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	u, ok := m.users[id]
	if !ok {
		return ErrNotFound
	}
	delete(m.usersByEmail, u.Email)
	delete(m.users, id)
	return nil
}

func (m *MemoryStore) CreateRefreshToken(t RefreshToken) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.refreshTokens[t.TokenHash] = t
	return nil
}

func (m *MemoryStore) GetRefreshToken(tokenHash string) (RefreshToken, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	t, ok := m.refreshTokens[tokenHash]
	if !ok {
		return RefreshToken{}, ErrNotFound
	}
	return t, nil
}

func (m *MemoryStore) RotateRefreshToken(oldHash string, newToken RefreshToken) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	old, ok := m.refreshTokens[oldHash]
	if !ok {
		return ErrNotFound
	}
	if old.Revoked {
		return ErrRevoked
	}
	if time.Now().UTC().After(old.ExpiresAt) {
		return ErrExpired
	}
	old.Revoked = true
	m.refreshTokens[oldHash] = old
	m.refreshTokens[newToken.TokenHash] = newToken
	return nil
}

func (m *MemoryStore) RevokeRefreshToken(tokenHash string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	t, ok := m.refreshTokens[tokenHash]
	if !ok {
		return ErrNotFound
	}
	t.Revoked = true
	m.refreshTokens[tokenHash] = t
	return nil
}

func (m *MemoryStore) CreateMachineClient(c MachineClient) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if _, exists := m.machineClients[c.ClientID]; exists {
		return ErrDuplicate
	}
	if c.CreatedAt.IsZero() {
		c.CreatedAt = time.Now().UTC()
	}
	m.machineClients[c.ClientID] = c
	return nil
}

func (m *MemoryStore) GetMachineClientByID(clientID string) (MachineClient, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	c, ok := m.machineClients[clientID]
	if !ok {
		return MachineClient{}, ErrNotFound
	}
	return c, nil
}
