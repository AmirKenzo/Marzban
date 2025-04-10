import re
from decimal import Decimal


class NumericValidatorMixin:
    @staticmethod
    def cast_to_int(v):
        """
        Static method to validate and convert numeric values to integers.

        Args:
            v: Input value to be converted

        Returns:
            int or None: Converted integer value

        Raises:
            ValueError: If the input cannot be converted to an integer
        """
        if v is None:  # Allow None values
            return v
        elif isinstance(v, float) or isinstance(v, Decimal):  # Allow float or Decimal to int conversion
            return int(v)
        elif isinstance(v, int):  # Allow integers directly
            return v

        raise ValueError("must be an integer, Decimal or a float, not a string")  # Reject strings
    
    @staticmethod
    def cast_to_float(v):
        """
        Static method to validate and convert numeric values to floats.

        Args:
            v: Input value to be converted

        Returns:
            float or None: Converted float value

        Raises:
            ValueError: If the input cannot be converted to an float
        """
        if v is None:
            return v
        elif isinstance(v, int) or isinstance(v, Decimal):
            return float(v)
        elif isinstance(v, float):
            return v

        raise ValueError("must be an integer, Decimal or a float, not a string") 


class ListValidator:
    @staticmethod
    def nullable_list(list: list | None, name: str) -> list:
        if list and len(list) < 1:
            raise ValueError(f"you must select at least one {name}")
        return list

    @staticmethod
    def not_null_list(list: list, name: str) -> list:
        if not list or len(list) < 1:
            raise ValueError(f"you must select at least one {name}")
        return list

    @staticmethod
    def deduplicate_values(values: list) -> list:
        """Remove duplicate values while preserving exact order"""
        return list(dict.fromkeys(values))


class PasswordValidator:
    @staticmethod
    def validate_password(value: str | None, check_username: str | None = None):
        if value is None:
            return value  # Allow None for optional passwords

        errors = []
        # Length check
        if len(value) < 12:
            errors.append("Password must be at least 12 characters long")
        # At least 2 digits
        if len(re.findall(r"\d", value)) < 2:
            errors.append("Password must contain at least 2 digits")
        # At least 2 uppercase letters
        if len(re.findall(r"[A-Z]", value)) < 2:
            errors.append("Password must contain at least 2 uppercase letters")
        # At least 2 lowercase letters
        if len(re.findall(r"[a-z]", value)) < 2:
            errors.append("Password must contain at least 2 lowercase letters")
        # At least 1 special character
        if not re.search(r"[!@#$%^&*()\-_=+\[\]{}|;:,.<>?/~`]", value):
            errors.append("Password must contain at least one special character")
        # Check if password contains the username
        if check_username and check_username.lower() in value.lower():
            errors.append("Password cannot contain the username")

        if errors:
            raise ValueError("; ".join(errors))
        return value
