package database

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

// Initialize sets up the database connection and creates tables if they don't exist
func Initialize(databaseURL string) (*sql.DB, error) {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Create tables if they don't exist
	if err := createTables(db); err != nil {
		return nil, fmt.Errorf("failed to create tables: %w", err)
	}

	return db, nil
}

func createTables(db *sql.DB) error {
	// Create users table
	usersTable := `
	CREATE TABLE IF NOT EXISTS users (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		phone_e164 TEXT NOT NULL,
		phone_hash BYTEA NOT NULL UNIQUE,
		created_at TIMESTAMPTZ DEFAULT NOW()
	);`

	// Create rooms table
	roomsTable := `
	CREATE TABLE IF NOT EXISTS rooms (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		name TEXT NOT NULL,
		owner_user_id UUID NOT NULL REFERENCES users(id),
		created_at TIMESTAMPTZ DEFAULT NOW()
	);`

	// Create room_memberships table
	membershipsTable := `
	CREATE TABLE IF NOT EXISTS room_memberships (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		room_id UUID NOT NULL REFERENCES rooms(id),
		user_id UUID NOT NULL REFERENCES users(id),
		role TEXT NOT NULL CHECK (role IN ('LANDLORD', 'TENANT')),
		created_at TIMESTAMPTZ DEFAULT NOW(),
		UNIQUE (room_id, user_id)
	);`

	// Create invites table
	invitesTable := `
	CREATE TABLE IF NOT EXISTS invites (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		room_id UUID NOT NULL REFERENCES rooms(id),
		phone_e164 TEXT NOT NULL,
		role TEXT NOT NULL CHECK (role IN ('LANDLORD', 'TENANT')),
		token UUID NOT NULL UNIQUE,
		status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACCEPTED', 'EXPIRED')),
		expires_at TIMESTAMPTZ NOT NULL,
		created_at TIMESTAMPTZ DEFAULT NOW()
	);`

	// Create indexes
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_room_memberships_user_id ON room_memberships(user_id);",
		"CREATE INDEX IF NOT EXISTS idx_room_memberships_room_id ON room_memberships(room_id);",
		"CREATE INDEX IF NOT EXISTS idx_invites_token ON invites(token);",
		"CREATE INDEX IF NOT EXISTS idx_invites_phone ON invites(phone_e164);",
		"CREATE INDEX IF NOT EXISTS idx_users_phone_hash ON users(phone_hash);",
	}

	// Execute table creation
	tables := []string{usersTable, roomsTable, membershipsTable, invitesTable}
	for _, table := range tables {
		if _, err := db.Exec(table); err != nil {
			return fmt.Errorf("failed to create table: %w", err)
		}
	}

	// Execute index creation
	for _, index := range indexes {
		if _, err := db.Exec(index); err != nil {
			return fmt.Errorf("failed to create index: %w", err)
		}
	}

	return nil
}
