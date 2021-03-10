from email_validator import validate_email, EmailNotValidError

email = "my+adprovideress@aol.com"

try:
  # Validate.
  valid = validate_email(email)

  # Update with the normalized form.
  email = valid.email
except EmailNotValidError as e:
  # email is not valid, exception message is human-readable
  print(str(e))
