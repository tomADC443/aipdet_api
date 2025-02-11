-- add a user to user table
-- Insert a new user into the "user" table.  Replace the placeholders with actual values.
INSERT INTO
    "user" (
        "email",
        "password",
        "first_name",
        "last_name",
        "verified",
        "verify_secret"
    )
VALUES
    (
        'test@test.de',
        '<hashed+saltedPW here>',
        'John',
        'Test',
        TRUE,
        'some_secret'
    );