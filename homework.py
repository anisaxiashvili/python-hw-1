import re
from functools import total_ordering
import unittest

@total_ordering
class Version:
    
    def __init__(self, version):
        self.version = version
        
        self.major = None
        self.minor = None
        self.patch = None
        self.pre_release = None
        self.pre_release_parts = None
        
        main_version, pre_release = self._split_version(version)
        self.major, self.minor, self.patch = self._parse_main_version(main_version)
        self.pre_release = pre_release
        self.pre_release_parts = self._parse_pre_release_parts(pre_release)
    
    def _split_version(self, version):
        """Split version string into main version and pre-release parts"""
        version = version.lstrip('v')
        
        if '-' in version:
            main_version, pre_release = version.split('-', 1)
            return main_version, pre_release
        
        match = re.match(r'^(\d+\.\d+\.\d+)([a-zA-Z].*)$', version)
        if match:
            main_version = match.group(1)
            pre_release = match.group(2)
            return main_version, pre_release
        
        return version, None
    
    def _parse_main_version(self, main_version):
        """Parse MAJOR.MINOR.PATCH version components and return them as tuple"""
        version_parts = main_version.split('.')
        while len(version_parts) < 3:
            version_parts.append('0')
        
        try:
            major = int(version_parts[0])
            minor = int(version_parts[1])
            patch = int(version_parts[2])
            return major, minor, patch
        except (ValueError, IndexError):
            raise ValueError(f"Invalid version format: {main_version}")
    
    def _parse_pre_release_parts(self, pre_release):
        """Parse pre-release identifiers and return parsed parts list"""
        if pre_release is None:
            return None
        
        parts = pre_release.split('.')
        parsed_parts = []
        
        for part in parts:
            numbers = re.findall(r'\d+', part)
            if numbers:
                parsed_parts.append((True, int(numbers[0]), part))
            else:
                parsed_parts.append((False, part, part))
        
        return parsed_parts
    
    def _has_pre_release(self):
        """Check if this version has pre-release identifiers"""
        return self.pre_release_parts is not None
    
    def _compare_pre_release(self, other):
        """Compare pre-release versions according to semver rules"""
        self_has_pre = self._has_pre_release()
        other_has_pre = other._has_pre_release()
        
        if not self_has_pre and not other_has_pre:
            return False  
        if not self_has_pre and other_has_pre:
            return False  
        if self_has_pre and not other_has_pre:
            return True 
        
        return self._compare_pre_release_parts(other)
    
    def _compare_pre_release_parts(self, other):
        """Compare pre-release parts when both versions have them"""
        max_parts = max(len(self.pre_release_parts), len(other.pre_release_parts))
        
        for i in range(max_parts):
            if i >= len(self.pre_release_parts):
                return True 
            if i >= len(other.pre_release_parts):
                return False
            
            self_part = self.pre_release_parts[i]
            other_part = other.pre_release_parts[i]
            
            part_comparison = self._compare_single_pre_release_part(self_part, other_part)
            if part_comparison is not None:
                return part_comparison
        
        return False 
    
    def _compare_single_pre_release_part(self, self_part, other_part):
        """Compare a single pre-release part, returns True if self < other, False if self > other, None if equal"""
        self_is_numeric, self_value, self_string = self_part
        other_is_numeric, other_value, other_string = other_part
        
        if self_is_numeric and not other_is_numeric:
            return True  
        if not self_is_numeric and other_is_numeric:
            return False 
        
        if self_is_numeric and other_is_numeric:
            if self_value < other_value:
                return True
            elif self_value > other_value:
                return False
            else:
                return None 
        
        if self_string < other_string:
            return True
        elif self_string > other_string:
            return False
        else:
            return None 
    
    def __eq__(self, other):
        if not isinstance(other, Version):
            return False
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch and 
                self.pre_release == other.pre_release)
    
    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        
        if self.major != other.major:
            return self.major < other.major
        
        if self.minor != other.minor:
            return self.minor < other.minor
        
        if self.patch != other.patch:
            return self.patch < other.patch
        
        return self._compare_pre_release(other)
    
    def __str__(self):
        return self.version
    
    def __repr__(self):
        return f"Version('{self.version}')"


class TestVersion(unittest.TestCase):
    """Comprehensive test suite for Version class"""
    
    def test_basic_comparison(self):
        """Test basic version comparisons"""
        self.assertTrue(Version('1.0.0') < Version('2.0.0'))
        self.assertTrue(Version('1.0.0') < Version('1.1.0'))
        self.assertTrue(Version('1.1.0') < Version('1.1.1'))
        self.assertFalse(Version('2.0.0') < Version('1.0.0'))
    
    def test_equality(self):
        """Test version equality"""
        self.assertEqual(Version('1.0.0'), Version('1.0.0'))
        self.assertNotEqual(Version('1.0.0'), Version('1.0.1'))
        self.assertNotEqual(Version('1.3.42'), Version('42.3.1'))
    
    def test_prerelease_vs_release(self):
        """Test that releases have higher precedence than pre-releases"""
        self.assertTrue(Version('1.0.0-alpha') < Version('1.0.0'))
        self.assertTrue(Version('1.0.0-beta') < Version('1.0.0'))
        self.assertTrue(Version('1.0.0-rc.1') < Version('1.0.0'))
        self.assertTrue(Version('0.3.0b') < Version('1.2.42'))
    
    def test_prerelease_comparison(self):
        """Test comparison between different pre-releases"""
        self.assertTrue(Version('1.0.0-alpha') < Version('1.0.0-alpha.1'))
        self.assertTrue(Version('1.0.0-alpha.1') < Version('1.0.0-beta'))
        self.assertTrue(Version('1.0.0-beta') < Version('1.0.0-rc'))
        self.assertTrue(Version('1.1.0-alpha') < Version('1.2.0-alpha.1'))
        self.assertTrue(Version('1.0.1b') < Version('1.0.10-alpha.beta'))
    
    def test_numeric_vs_string_prerelease(self):
        """Test numeric vs string pre-release identifiers"""
        self.assertTrue(Version('1.0.0-1') < Version('1.0.0-alpha'))
        self.assertTrue(Version('1.0.0-2') < Version('1.0.0-10'))
        self.assertTrue(Version('1.0.0-alpha') < Version('1.0.0-beta'))
    
    def test_edge_cases(self):
        """Test edge cases and special formats"""
        self.assertEqual(Version('1.0.0-alpha'), Version('1.0.0-alpha'))
        self.assertTrue(Version('1.0.0alpha') < Version('1.0.0-beta'))
        self.assertTrue(Version('2.0.0b1') < Version('2.0.0'))
        self.assertEqual(Version('1.0'), Version('1.0.0'))
        self.assertTrue(Version('1') < Version('1.1'))
    
    def test_original_test_cases(self):
        """Test the original provided test cases"""
        to_test = [
            ("1.0.0", "2.0.0"),
            ("1.0.0", "1.42.0"),
            ("1.2.0", "1.2.42"),
            ("1.1.0-alpha", "1.2.0-alpha.1"),
            ("1.0.1b", "1.0.10-alpha.beta"),
            ("1.0.0-rc.1", "1.0.0"),
        ]
        
        for left, right in to_test:
            with self.subTest(left=left, right=right):
                self.assertLess(Version(left), Version(right))
                self.assertGreater(Version(right), Version(left))
                self.assertNotEqual(Version(right), Version(left))
    
    def test_example_cases(self):
        """Test the example cases from the docstring"""
        self.assertTrue(Version('1.1.3') < Version('2.2.3'))
        self.assertTrue(Version('1.3.0') > Version('0.3.0'))
        self.assertTrue(Version('0.3.0b') < Version('1.2.42'))
        self.assertFalse(Version('1.3.42') == Version('42.3.1'))


def main():
    """Run basic examples and all tests"""
    print("Running basic examples:")
    print(f"Version('1.1.3') < Version('2.2.3'): {Version('1.1.3') < Version('2.2.3')}")
    print(f"Version('1.3.0') > Version('0.3.0'): {Version('1.3.0') > Version('0.3.0')}")
    print(f"Version('0.3.0b') < Version('1.2.42'): {Version('0.3.0b') < Version('1.2.42')}")
    print(f"Version('1.3.42') == Version('42.3.1'): {Version('1.3.42') == Version('42.3.1')}")
    
    print("\nRunning comprehensive test suite...")
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    main()