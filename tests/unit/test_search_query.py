"""
Unit tests for SearchQuery value object
"""

import pytest

from src.core.domain.value_objects import SearchQuery


class TestSearchQuery:
    """Tests for SearchQuery value object"""
    
    def test_create_arabic_query(self):
        """Test creating an Arabic search query"""
        query = SearchQuery(raw_query="العادات الذرية", language="ar")
        
        assert query.raw_query == "العادات الذرية"
        assert query.language == "ar"
        assert query.formatted_query == "ملخص كتاب العادات الذرية"
    
    def test_create_english_query(self):
        """Test creating an English search query"""
        query = SearchQuery(raw_query="Atomic Habits", language="en")
        
        assert query.raw_query == "Atomic Habits"
        assert query.language == "en"
        assert query.formatted_query == "Atomic Habits book summary"
    
    def test_create_query_empty_raises_error(self):
        """Test that empty query raises ValueError"""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            SearchQuery(raw_query="")
    
    def test_create_query_invalid_language_raises_error(self):
        """Test that invalid language raises ValueError"""
        with pytest.raises(ValueError, match="Invalid language"):
            SearchQuery(raw_query="Test", language="fr")
    
    def test_max_results_validation(self):
        """Test max_results validation"""
        # Valid range
        query = SearchQuery(raw_query="Test", max_results=10)
        assert query.max_results == 10
        
        # Too small
        with pytest.raises(ValueError, match="max_results must be between"):
            SearchQuery(raw_query="Test", max_results=0)
        
        # Too large
        with pytest.raises(ValueError, match="max_results must be between"):
            SearchQuery(raw_query="Test", max_results=51)
    
    def test_safe_filename(self):
        """Test safe filename generation"""
        query = SearchQuery(raw_query="Atomic Habits: Building Better Habits")
        
        safe = query.safe_filename
        
        # Should remove special characters
        assert ":" not in safe
        # Should replace spaces with hyphens
        assert "-" in safe
        assert "Atomic" in safe
        assert "Habits" in safe
    
    def test_with_max_results(self):
        """Test creating new query with different max_results"""
        query1 = SearchQuery(raw_query="Test", max_results=10)
        query2 = query1.with_max_results(20)
        
        assert query1.max_results == 10
        assert query2.max_results == 20
        assert query1.raw_query == query2.raw_query
    
    def test_immutable(self):
        """Test that SearchQuery is immutable (frozen dataclass)"""
        query = SearchQuery(raw_query="Test")
        
        with pytest.raises(Exception):  # FrozenInstanceError
            query.raw_query = "Changed"
    
    def test_str_representation(self):
        """Test string representation"""
        query = SearchQuery(raw_query="Test Book", language="ar")
        
        assert str(query) == "ملخص كتاب Test Book"
