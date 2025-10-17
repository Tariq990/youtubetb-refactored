"""
Unified Output Management System.

This module provides a centralized system for managing all outputs:
- Console output with rich formatting
- File output (logs, results, reports)
- Progress tracking
- Status updates
- Result formatting

Usage:
    from src.shared.output import get_output_manager
    
    output = get_output_manager()
    
    output.print_header("Starting Pipeline")
    output.print_info("Processing video...")
    output.print_success("Video processed successfully!")
    
    with output.progress("Downloading videos", total=10) as progress:
        for i in range(10):
            # Do work
            progress.update(1)
"""

from __future__ import annotations
from typing import Optional, Any, ContextManager, List
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
import json

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.tree import Tree
from rich.syntax import Syntax

from src.shared.logging import get_logger


logger = get_logger(__name__)


class OutputManager:
    """
    Centralized output management system.
    
    Provides:
    - Formatted console output
    - Progress tracking
    - File output management
    - Result formatting
    - Status updates
    """
    
    def __init__(
        self,
        console: Optional[Console] = None,
        output_dir: Optional[Path] = None,
        enable_file_output: bool = True,
    ):
        """
        Initialize output manager.
        
        Args:
            console: Rich console instance (creates new if None)
            output_dir: Directory for file outputs
            enable_file_output: Whether to save outputs to files
        """
        self.console = console or Console()
        self.output_dir = output_dir
        self.enable_file_output = enable_file_output
        
        if self.enable_file_output and self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== Console Output ====================
    
    def print_header(self, text: str, style: str = "bold cyan") -> None:
        """
        Print a header.
        
        Args:
            text: Header text
            style: Rich style
        """
        self.console.print()
        self.console.rule(f"[{style}]{text}[/{style}]")
        self.console.print()
    
    def print_info(self, message: str, **kwargs: Any) -> None:
        """
        Print info message.
        
        Args:
            message: Message text
            **kwargs: Additional key-value pairs to display
        """
        formatted = self._format_message("ℹ️", "blue", message, kwargs)
        self.console.print(formatted)
    
    def print_success(self, message: str, **kwargs: Any) -> None:
        """
        Print success message.
        
        Args:
            message: Message text
            **kwargs: Additional key-value pairs to display
        """
        formatted = self._format_message("✓", "green", message, kwargs)
        self.console.print(formatted)
    
    def print_warning(self, message: str, **kwargs: Any) -> None:
        """
        Print warning message.
        
        Args:
            message: Message text
            **kwargs: Additional key-value pairs to display
        """
        formatted = self._format_message("⚠️", "yellow", message, kwargs)
        self.console.print(formatted)
    
    def print_error(self, message: str, **kwargs: Any) -> None:
        """
        Print error message.
        
        Args:
            message: Message text
            **kwargs: Additional key-value pairs to display
        """
        formatted = self._format_message("✗", "red", message, kwargs)
        self.console.print(formatted)
    
    def print_step(self, step: int, total: int, message: str) -> None:
        """
        Print step indicator.
        
        Args:
            step: Current step number
            total: Total number of steps
            message: Step description
        """
        self.console.print(
            f"[bold cyan]Step {step}/{total}:[/bold cyan] {message}"
        )
    
    def _format_message(
        self,
        icon: str,
        color: str,
        message: str,
        kwargs: dict[str, Any]
    ) -> str:
        """Format message with icon and optional key-value pairs"""
        formatted = f"[{color}]{icon}[/{color}] {message}"
        
        if kwargs:
            details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            formatted += f" [dim]({details})[/dim]"
        
        return formatted
    
    # ==================== Progress Tracking ====================
    
    @contextmanager
    def progress(
        self,
        description: str,
        total: Optional[int] = None,
    ) -> ContextManager[Progress]:
        """
        Context manager for progress tracking.
        
        Args:
            description: Progress description
            total: Total number of items (None for indeterminate)
        
        Yields:
            Progress instance
        
        Example:
            with output.progress("Processing", total=100) as progress:
                task = progress.add_task(description, total=100)
                for i in range(100):
                    # Do work
                    progress.update(task, advance=1)
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        
        with progress:
            task = progress.add_task(description, total=total)
            
            class ProgressWrapper:
                def __init__(self, progress, task):
                    self._progress = progress
                    self._task = task
                
                def update(self, advance: int = 1, **kwargs: Any) -> None:
                    self._progress.update(self._task, advance=advance, **kwargs)
                
                def set_description(self, description: str) -> None:
                    self._progress.update(self._task, description=description)
            
            yield ProgressWrapper(progress, task)
    
    @contextmanager
    def spinner(self, message: str) -> ContextManager[None]:
        """
        Context manager for spinner.
        
        Args:
            message: Spinner message
        
        Yields:
            None
        
        Example:
            with output.spinner("Loading..."):
                # Do work
                pass
        """
        with self.console.status(f"[bold blue]{message}[/bold blue]"):
            yield
    
    # ==================== Tables ====================
    
    def print_table(
        self,
        title: str,
        columns: List[str],
        rows: List[List[Any]],
        show_header: bool = True,
    ) -> None:
        """
        Print a formatted table.
        
        Args:
            title: Table title
            columns: Column names
            rows: Table rows
            show_header: Whether to show header
        """
        table = Table(title=title, show_header=show_header)
        
        for column in columns:
            table.add_column(column, style="cyan")
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def print_dict(self, title: str, data: dict[str, Any]) -> None:
        """
        Print dictionary as table.
        
        Args:
            title: Table title
            data: Dictionary to display
        """
        rows = [[k, str(v)] for k, v in data.items()]
        self.print_table(title, ["Key", "Value"], rows)
    
    # ==================== Panels ====================
    
    def print_panel(
        self,
        content: str,
        title: Optional[str] = None,
        style: str = "blue",
    ) -> None:
        """
        Print content in a panel.
        
        Args:
            content: Panel content
            title: Panel title
            style: Panel style
        """
        panel = Panel(
            content,
            title=title,
            border_style=style,
        )
        self.console.print(panel)
    
    # ==================== Tree ====================
    
    def print_tree(self, title: str, tree_data: dict[str, Any]) -> None:
        """
        Print hierarchical data as tree.
        
        Args:
            title: Tree title
            tree_data: Nested dictionary representing tree structure
        """
        tree = Tree(f"[bold]{title}[/bold]")
        self._add_tree_nodes(tree, tree_data)
        self.console.print(tree)
    
    def _add_tree_nodes(self, tree: Tree, data: dict[str, Any]) -> None:
        """Recursively add nodes to tree"""
        for key, value in data.items():
            if isinstance(value, dict):
                branch = tree.add(f"[cyan]{key}[/cyan]")
                self._add_tree_nodes(branch, value)
            else:
                tree.add(f"[cyan]{key}:[/cyan] {value}")
    
    # ==================== Code Display ====================
    
    def print_code(
        self,
        code: str,
        language: str = "python",
        theme: str = "monokai",
    ) -> None:
        """
        Print syntax-highlighted code.
        
        Args:
            code: Code to display
            language: Programming language
            theme: Syntax theme
        """
        syntax = Syntax(code, language, theme=theme, line_numbers=True)
        self.console.print(syntax)
    
    # ==================== File Output ====================
    
    def save_json(
        self,
        filename: str,
        data: Any,
        indent: int = 2,
    ) -> Optional[Path]:
        """
        Save data as JSON file.
        
        Args:
            filename: Output filename
            data: Data to save
            indent: JSON indentation
        
        Returns:
            Path to saved file or None if disabled
        """
        if not self.enable_file_output or not self.output_dir:
            return None
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        logger.debug(f"Saved JSON to {output_path}")
        return output_path
    
    def save_text(
        self,
        filename: str,
        content: str,
    ) -> Optional[Path]:
        """
        Save text to file.
        
        Args:
            filename: Output filename
            content: Text content
        
        Returns:
            Path to saved file or None if disabled
        """
        if not self.enable_file_output or not self.output_dir:
            return None
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"Saved text to {output_path}")
        return output_path
    
    def save_report(
        self,
        title: str,
        sections: dict[str, str],
    ) -> Optional[Path]:
        """
        Save formatted report.
        
        Args:
            title: Report title
            sections: Dictionary of section_name -> content
        
        Returns:
            Path to saved file or None if disabled
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.md"
        
        content = f"# {title}\n\n"
        content += f"**Generated:** {datetime.now().isoformat()}\n\n"
        content += "---\n\n"
        
        for section_name, section_content in sections.items():
            content += f"## {section_name}\n\n"
            content += f"{section_content}\n\n"
        
        return self.save_text(filename, content)
    
    # ==================== Summary ====================
    
    def print_summary(
        self,
        title: str,
        data: dict[str, Any],
        style: str = "green",
    ) -> None:
        """
        Print summary panel.
        
        Args:
            title: Summary title
            data: Summary data
            style: Panel style
        """
        content = "\n".join(f"[cyan]{k}:[/cyan] {v}" for k, v in data.items())
        self.print_panel(content, title=title, style=style)


# Global output manager instance
_output_manager: Optional[OutputManager] = None


def get_output_manager(
    output_dir: Optional[Path] = None
) -> OutputManager:
    """
    Get global output manager instance.
    
    Args:
        output_dir: Directory for file outputs
    
    Returns:
        OutputManager instance
    """
    global _output_manager
    if _output_manager is None:
        _output_manager = OutputManager(output_dir=output_dir)
    return _output_manager

