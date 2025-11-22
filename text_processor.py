"""
Text processing module for cleaning and extracting information from text.
"""

import re
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class TextProcessingError(Exception):
    """Custom exception for text processing errors"""
    pass


class TextProcessor:
    """Utility class for text processing operations"""

    # Regex patterns for extraction
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )

    # More flexible phone patterns
    PHONE_PATTERNS = [
        # Standard formats with separators
        re.compile(r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'),
        # 10 consecutive digits
        re.compile(r'\b(\d{3})(\d{3})(\d{4})\b'),
        # With common prefixes
        re.compile(r'(?:phone|tel|mobile|cell)[\s:]*(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})', re.IGNORECASE),
    ]

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """
        Clean and normalize whitespace in text.

        Args:
            text: Input text to clean

        Returns:
            str: Text with normalized whitespace

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Split and rejoin to remove multiple spaces
        words = text.split()
        text = ' '.join(words)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def clean_newlines(text: str) -> str:
        """
        Clean excessive newlines in text.

        Args:
            text: Input text to clean

        Returns:
            str: Text with normalized newlines (max 2 consecutive)

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        # Replace multiple newlines with double newlines
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')

        return text

    @staticmethod
    def remove_special_characters(text: str, keep_chars: Optional[str] = None) -> str:
        """
        Remove special characters from text, keeping only specified characters.

        Args:
            text: Input text to clean
            keep_chars: Optional string of additional characters to keep

        Returns:
            str: Text with special characters removed

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        # Default allowed characters
        allowed = (
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '0123456789'
            ' \n.,!?-:;()@#$%&+='
        )

        # Add any additional characters to keep
        if keep_chars:
            allowed += keep_chars

        # Filter characters
        cleaned = ''.join(char for char in text if char in allowed)

        return cleaned

    @staticmethod
    def to_lowercase(text: str) -> str:
        """
        Convert text to lowercase.

        Args:
            text: Input text

        Returns:
            str: Lowercase text

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        return text.lower()

    @staticmethod
    def find_email(text: str) -> Optional[str]:
        """
        Extract email address from text using regex.

        Args:
            text: Input text to search

        Returns:
            str or None: First email address found, or None if no email found

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        match = TextProcessor.EMAIL_PATTERN.search(text)

        if match:
            email = match.group(0)
            logger.debug(f"Found email: {email}")
            return email

        logger.debug("No email found in text")
        return None

    @staticmethod
    def find_all_emails(text: str) -> List[str]:
        """
        Extract all email addresses from text.

        Args:
            text: Input text to search

        Returns:
            List[str]: List of all email addresses found

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        emails = TextProcessor.EMAIL_PATTERN.findall(text)
        logger.debug(f"Found {len(emails)} email(s)")
        return emails

    @staticmethod
    def find_phone(text: str) -> Optional[str]:
        """
        Extract phone number from text using multiple pattern matching strategies.

        Args:
            text: Input text to search

        Returns:
            str or None: First phone number found (formatted), or None if no phone found

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        # Try each pattern
        for pattern in TextProcessor.PHONE_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    area_code, prefix, line = groups[:3]
                    phone = f"({area_code}) {prefix}-{line}"
                    logger.debug(f"Found phone: {phone}")
                    return phone

        # Fallback: Look for any 10-digit sequence
        digits_only = ''.join(c for c in text if c.isdigit())
        if len(digits_only) >= 10:
            # Take first 10 digits
            area_code = digits_only[0:3]
            prefix = digits_only[3:6]
            line = digits_only[6:10]
            phone = f"({area_code}) {prefix}-{line}"
            logger.debug(f"Found phone via digit extraction: {phone}")
            return phone

        logger.debug("No phone number found in text")
        return None

    @staticmethod
    def find_all_phones(text: str) -> List[str]:
        """
        Extract all phone numbers from text.

        Args:
            text: Input text to search

        Returns:
            List[str]: List of all phone numbers found (formatted)

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        phones = []

        # Try each pattern
        for pattern in TextProcessor.PHONE_PATTERNS:
            matches = pattern.finditer(text)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 3:
                    area_code, prefix, line = groups[:3]
                    phone = f"({area_code}) {prefix}-{line}"
                    if phone not in phones:  # Avoid duplicates
                        phones.append(phone)

        logger.debug(f"Found {len(phones)} phone number(s)")
        return phones

    @staticmethod
    def has_section(text: str, section_name: str) -> bool:
        """
        Check if a section name exists in text (case-insensitive).

        Args:
            text: Text to search in
            section_name: Section name to search for

        Returns:
            bool: True if section name is found, False otherwise

        Raises:
            TextProcessingError: If inputs are not strings
        """
        if not isinstance(text, str) or not isinstance(section_name, str):
            raise TextProcessingError(
                "Both text and section_name must be strings"
            )

        text_lower = text.lower()
        section_lower = section_name.lower()

        return section_lower in text_lower

    @staticmethod
    def find_sections(text: str, section_names: List[str]) -> Dict[str, bool]:
        """
        Check for multiple sections in text.

        Args:
            text: Text to search in
            section_names: List of section names to search for

        Returns:
            Dict mapping section names to their presence (True/False)

        Raises:
            TextProcessingError: If inputs are invalid
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected text to be string, got {type(text).__name__}"
            )

        if not isinstance(section_names, list):
            raise TextProcessingError(
                f"Expected section_names to be list, got {type(section_names).__name__}"
            )

        return {
            section: TextProcessor.has_section(text, section)
            for section in section_names
        }

    @staticmethod
    def preprocess(text: str, remove_special: bool = True) -> str:
        """
        Apply standard preprocessing pipeline to text.

        Pipeline steps:
        1. Clean whitespace
        2. Clean newlines
        3. Remove special characters (optional)
        4. Clean whitespace again

        Args:
            text: Input text to process
            remove_special: Whether to remove special characters (default: True)

        Returns:
            str: Preprocessed text

        Raises:
            TextProcessingError: If text is not a string or processing fails
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        try:
            # Step 1: Clean whitespace
            text = TextProcessor.clean_whitespace(text)

            # Step 2: Clean newlines
            text = TextProcessor.clean_newlines(text)

            # Step 3: Remove special characters (optional)
            if remove_special:
                text = TextProcessor.remove_special_characters(text)

            # Step 4: Clean whitespace again
            text = TextProcessor.clean_whitespace(text)

            return text

        except Exception as e:
            raise TextProcessingError(
                f"Failed to preprocess text: {str(e)}"
            ) from e

    @staticmethod
    def get_stats(text: str) -> Dict[str, int | bool]:
        """
        Get statistics about the text.

        Args:
            text: Input text to analyze

        Returns:
            Dict containing text statistics

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        words = text.split()

        return {
            'characters': len(text),
            'words': len(words),
            'lines': text.count('\n') + 1,
            'has_email': bool(TextProcessor.EMAIL_PATTERN.search(text)),
            'has_phone': bool(TextProcessor.find_phone(text)),
            'email_count': len(TextProcessor.find_all_emails(text)),
            'phone_count': len(TextProcessor.find_all_phones(text))
        }

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, Optional[str] | List[str]]:
        """
        Extract all contact information from text.

        Args:
            text: Input text to search

        Returns:
            Dict containing extracted contact information

        Raises:
            TextProcessingError: If text is not a string
        """
        if not isinstance(text, str):
            raise TextProcessingError(
                f"Expected string, got {type(text).__name__}"
            )

        return {
            'primary_email': TextProcessor.find_email(text),
            'all_emails': TextProcessor.find_all_emails(text),
            'primary_phone': TextProcessor.find_phone(text),
            'all_phones': TextProcessor.find_all_phones(text)
        }