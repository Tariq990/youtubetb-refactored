"""
Process Book Use Case

Main business logic for processing a book into a video.
"""

from __future__ import annotations
from typing import Protocol, Optional
from pathlib import Path

from ...core.domain.entities import Book, Video, Script, Audio
from ...core.domain.value_objects import ProcessingConfig, VideoMetadata


class TranscriptPort(Protocol):
    """Port for getting video transcripts."""
    
    def get_transcript(self, video: Video) -> str:
        """Get transcript for a video."""
        ...


class ScriptGeneratorPort(Protocol):
    """Port for generating scripts."""
    
    def generate_script(self, transcript: str, book_title: str, language: str) -> Script:
        """Generate a script from transcript."""
        ...


class TTSPort(Protocol):
    """Port for text-to-speech."""
    
    def generate_audio(self, script: Script, output_path: Path) -> Audio:
        """Generate audio from script."""
        ...


class VideoRendererPort(Protocol):
    """Port for video rendering."""
    
    def render_video(
        self,
        audio: Audio,
        book: Book,
        output_path: Path,
        config: ProcessingConfig
    ) -> Path:
        """Render video with audio."""
        ...


class ThumbnailGeneratorPort(Protocol):
    """Port for thumbnail generation."""
    
    def generate_thumbnail(
        self,
        book: Book,
        output_path: Path
    ) -> Path:
        """Generate thumbnail for video."""
        ...


class VideoUploaderPort(Protocol):
    """Port for uploading videos."""
    
    def upload(
        self,
        video_path: Path,
        metadata: VideoMetadata,
        thumbnail_path: Optional[Path] = None
    ) -> str:
        """Upload video to YouTube. Returns video URL."""
        ...


class ProcessBookUseCase:
    """
    Use case for processing a book into a YouTube video.
    
    This orchestrates the entire pipeline:
    1. Get video transcript
    2. Generate script using AI
    3. Generate audio using TTS
    4. Render video
    5. Generate thumbnail
    6. Upload to YouTube
    """
    
    def __init__(
        self,
        transcript_adapter: TranscriptPort,
        script_generator: ScriptGeneratorPort,
        tts_adapter: TTSPort,
        video_renderer: VideoRendererPort,
        thumbnail_generator: ThumbnailGeneratorPort,
        video_uploader: VideoUploaderPort,
        config: ProcessingConfig,
    ):
        """Initialize use case with required adapters."""
        self.transcript_adapter = transcript_adapter
        self.script_generator = script_generator
        self.tts_adapter = tts_adapter
        self.video_renderer = video_renderer
        self.thumbnail_generator = thumbnail_generator
        self.video_uploader = video_uploader
        self.config = config
    
    def execute(
        self,
        book: Book,
        selected_video: Video,
        output_dir: Path,
        upload: bool = True,
    ) -> Book:
        """
        Process a book into a YouTube video.
        
        Args:
            book: Book entity to process
            selected_video: Source video for transcript
            output_dir: Directory for output files
            upload: Whether to upload to YouTube
        
        Returns:
            Updated book entity
        
        Raises:
            PipelineException: If processing fails
        """
        try:
            # Mark book as processing
            book.mark_as_processing(str(output_dir))
            
            # Step 1: Get transcript
            print(f"📝 Getting transcript for {selected_video.title}...")
            transcript = self.transcript_adapter.get_transcript(selected_video)
            
            # Step 2: Generate script
            print(f"🤖 Generating script using {self.config.gemini_model}...")
            script = self.script_generator.generate_script(
                transcript,
                book.title,
                book.language
            )
            
            # Clean and truncate script
            script.clean_markers()
            if not script.is_within_limit(self.config.max_script_length):
                script.truncate(self.config.max_script_length)
            
            # Save script
            script_path = output_dir / "script.txt"
            script_path.write_text(script.content, encoding="utf-8")
            
            # Step 3: Generate audio
            print(f"🎵 Generating audio...")
            audio_path = output_dir / "audio.mp3"
            audio = self.tts_adapter.generate_audio(script, audio_path)
            
            # Step 4: Render video
            print(f"🎬 Rendering video...")
            video_path = output_dir / "final_video.mp4"
            final_video = self.video_renderer.render_video(
                audio,
                book,
                video_path,
                self.config
            )
            
            # Step 5: Generate thumbnail
            print(f"🖼️ Generating thumbnail...")
            thumbnail_path = output_dir / "thumbnail.png"
            thumbnail = self.thumbnail_generator.generate_thumbnail(
                book,
                thumbnail_path
            )
            
            # Mark as done
            book.mark_as_done()
            
            # Step 6: Upload if requested
            if upload:
                print(f"📤 Uploading to YouTube...")
                metadata = VideoMetadata.from_book(
                    book.title,
                    book.author,
                    book.language
                )
                youtube_url = self.video_uploader.upload(
                    final_video,
                    metadata,
                    thumbnail
                )
                book.mark_as_uploaded(youtube_url)
                print(f"✅ Uploaded: {youtube_url}")
            
            return book
            
        except Exception as e:
            # Mark book as failed
            book.mark_as_failed(str(e))
            raise
