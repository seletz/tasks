"""Generate the code reference pages and navigation."""

import logging
import sys
from pathlib import Path

import mkdocs_gen_files

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_reference_pages():
    """Generate reference documentation for Python modules."""
    nav = mkdocs_gen_files.Nav()
    src = Path("packages/journal-lib/src")
    
    # Validate source directory exists
    if not src.exists():
        logger.error(f"Source directory {src} does not exist")
        sys.exit(1)
    
    if not src.is_dir():
        logger.error(f"Source path {src} is not a directory")
        sys.exit(1)
    
    python_files = list(src.rglob("*.py"))
    if not python_files:
        logger.warning(f"No Python files found in {src}")
        return
    
    logger.info(f"Found {len(python_files)} Python files to process")
    
    for path in sorted(python_files):
        try:
            # Skip test files and private modules
            if "test" in path.name or path.name.startswith("_") and path.name != "__init__.py":
                logger.debug(f"Skipping {path}")
                continue
            
            module_path = path.relative_to(src).with_suffix("")
            doc_path = path.relative_to(src).with_suffix(".md")
            full_doc_path = Path("reference", doc_path)
            
            parts = tuple(module_path.parts)
            
            # Handle special files
            if parts[-1] == "__init__":
                # Convert __init__.py to index.md
                parts = parts[:-1]
                doc_path = doc_path.with_name("index.md")
                full_doc_path = full_doc_path.with_name("index.md")
            elif parts[-1] == "__main__":
                logger.debug(f"Skipping __main__ module: {path}")
                continue
            
            if not parts:
                logger.debug(f"Skipping root __init__.py: {path}")
                continue
            
            nav[parts] = doc_path.as_posix()
            
            # Generate documentation file
            with mkdocs_gen_files.open(full_doc_path, "w") as fd:
                ident = ".".join(parts)
                fd.write(f"::: {ident}")
            
            mkdocs_gen_files.set_edit_path(full_doc_path, path)
            logger.debug(f"Generated documentation for {ident}")
            
        except Exception as e:
            logger.error(f"Failed to process {path}: {e}")
            # Continue processing other files instead of failing completely
            continue
    
    # Generate navigation file
    try:
        with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
            nav_file.writelines(nav.build_literate_nav())
        
        # Count processed modules by counting nav items
        module_count = len([k for k in nav.items()])
        logger.info(f"Generated reference documentation for {module_count} modules")
    except Exception as e:
        logger.error(f"Failed to generate navigation file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_reference_pages()


# Call the function when imported as a module
generate_reference_pages()