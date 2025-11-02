
class TextProcessor:
    def clean_whitespace(text):
        text = text.replace('\t', ' ')
        words = text.split()
        text = ' '.join(words)

        text = text.strip()

        return text

    def clean_newlines(text):
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')

        return text

    def remove_special_characters(text):
        allowed = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n.,!?-:;()@#$%&+='
        cleaned = ''
        for char in text:
            if char in allowed:
                cleaned += char
        return cleaned

    def to_lowercase(text):
        return text.lower()

    def find_email(text):
        words = text.split()
        for word in words:
            if '@' in word and '.' in word:
                email = word.strip('.,;:!?()')
                return email
        return None

    def find_phone(text):
        text = text.replace('\n', ' ')
        words = text.split()
        for i in range(len(words) - 1):
            combined = words[i] + ' ' + words[i + 1]
            digit_count = sum(1 for char in combined if char.isdigit())
            if digit_count == 10:
                return combined.strip()
        for word in words:
            digit_count = sum(1 for char in word if char.isdigit())
            if digit_count == 10:
                return word
        if 'Phone:' in text or 'phone:' in text.lower():
            # Find the position of "Phone:"
            phone_index = text.lower().find('phone:')
            if phone_index != -1:
                after_phone = text[phone_index + 6:phone_index + 50]
                digits = ''
                for char in after_phone:
                    if char.isdigit():
                        digits += char
                        if len(digits) == 10:
                            phone_section = after_phone[:after_phone.find(digits[-1]) + 1]
                            phone_parts = phone_section.split()
                            if phone_parts:
                                result = ''
                                for part in phone_parts[:3]:
                                    result += part + ' '
                                    if sum(1 for c in result if c.isdigit()) >= 10:
                                        return result.strip()

        return None

    def has_section(text, section_name):
        text_lower = text.lower()
        section_lower = section_name.lower()
        return section_lower in text_lower

    def preprocess(text):
        """
        Pre-processing steps:
        1) Clean whitespace
        2) Clean newlines
        3) Remove special characters
        4) Clean whitespace again (after removing special characters)
        """
        text = TextProcessor.clean_whitespace(text)
        text = TextProcessor.clean_newlines(text)
        text = TextProcessor.remove_special_characters(text)
        text = TextProcessor.clean_whitespace(text)

        return text

    def get_stats(text):
        """Get statistics about the text"""
        words = text.split()
        return {
            'characters': len(text),
            'words': len(words),
            'lines': text.count('\n') + 1,
            'has_email': '@' in text,
            'has_phone': any(char.isdigit() for char in text)
        }
