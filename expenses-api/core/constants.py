"""
Temporary constants for development.
TODO: Remove this file once authentication is implemented.
"""
import uuid

# Test user ID used for all operations until authentication is implemented.
# This user must exist in the database (seeded via migration).
TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID_BYTES = TEST_USER_ID.bytes
