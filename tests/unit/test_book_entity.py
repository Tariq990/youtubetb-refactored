"""
Unit tests for Book entity
"""

import pytest
from datetime import datetime
from uuid import UUID

from src.core.domain.entities import Book


class TestBookEntity:
    """Tests for Book entity"""
    
    def test_create_book_with_defaults(self):
        """Test creating a book with default values"""
        book = Book(title="Atomic Habits")
        
        assert book.title == "Atomic Habits"
        assert book.author is None
        assert book.language == "ar"
        assert book.status == "pending"
        assert isinstance(book.id, UUID)
        assert isinstance(book.created_at, datetime)
    
    def test_create_book_with_author(self):
        """Test creating a book with author"""
        book = Book(
            title="Deep Work",
            author="Cal Newport"
        )
        
        assert book.title == "Deep Work"
        assert book.author == "Cal Newport"
    
    def test_create_book_empty_title_raises_error(self):
        """Test that empty title raises ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            Book(title="")
    
    def test_create_book_invalid_status_raises_error(self):
        """Test that invalid status raises ValueError"""
        with pytest.raises(ValueError, match="Invalid status"):
            Book(title="Test Book", status="invalid_status")
    
    def test_create_book_invalid_language_raises_error(self):
        """Test that invalid language raises ValueError"""
        with pytest.raises(ValueError, match="Invalid language"):
            Book(title="Test Book", language="fr")
    
    def test_mark_as_processing(self):
        """Test marking book as processing"""
        book = Book(title="Test Book")
        book.mark_as_processing("/path/to/run")
        
        assert book.status == "processing"
        assert book.run_folder == "/path/to/run"
    
    def test_mark_as_done(self):
        """Test marking book as done"""
        book = Book(title="Test Book")
        book.mark_as_done()
        
        assert book.status == "done"
    
    def test_mark_as_uploaded(self):
        """Test marking book as uploaded"""
        book = Book(title="Test Book")
        youtube_url = "https://youtube.com/watch?v=abc123"
        playlist_id = "PL123"
        
        book.mark_as_uploaded(youtube_url, playlist_id)
        
        assert book.status == "uploaded"
        assert book.youtube_url == youtube_url
        assert book.playlist_id == playlist_id
    
    def test_mark_as_failed(self):
        """Test marking book as failed"""
        book = Book(title="Test Book")
        error_msg = "Processing failed"
        
        book.mark_as_failed(error_msg)
        
        assert book.status == "failed"
        assert book.error_message == error_msg
    
    def test_is_completed(self):
        """Test is_completed method"""
        book = Book(title="Test Book")
        
        assert not book.is_completed()
        
        book.mark_as_done()
        assert book.is_completed()
        
        book2 = Book(title="Test Book 2")
        book2.mark_as_uploaded("https://youtube.com/watch?v=xyz")
        assert book2.is_completed()
    
    def test_is_processing(self):
        """Test is_processing method"""
        book = Book(title="Test Book")
        
        assert not book.is_processing()
        
        book.mark_as_processing("/path")
        assert book.is_processing()
    
    def test_is_failed(self):
        """Test is_failed method"""
        book = Book(title="Test Book")
        
        assert not book.is_failed()
        
        book.mark_as_failed("Error")
        assert book.is_failed()
    
    def test_to_dict(self):
        """Test converting book to dictionary"""
        book = Book(
            title="Test Book",
            author="Test Author",
            language="en"
        )
        
        data = book.to_dict()
        
        assert data["title"] == "Test Book"
        assert data["author"] == "Test Author"
        assert data["language"] == "en"
        assert "id" in data
        assert "created_at" in data
    
    def test_from_dict(self):
        """Test creating book from dictionary"""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "language": "en",
            "status": "done"
        }
        
        book = Book.from_dict(data)
        
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.language == "en"
        assert book.status == "done"
    
    def test_repr(self):
        """Test string representation"""
        book = Book(title="Test Book", author="Test Author")
        
        repr_str = repr(book)
        
        assert "Test Book" in repr_str
        assert "Test Author" in repr_str
        assert "pending" in repr_str
