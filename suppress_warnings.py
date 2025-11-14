# Utility module to suppress harmless customtkinter callback warnings
import sys
import os
import io


def run_with_warning_suppression(root_window):
    """Run mainloop with 'invalid command name' warnings suppressed by redirecting stderr."""
    # Save original stderr
    original_stderr = sys.stderr
    original_stderr_fd = os.dup(2)  # File descriptor for stderr

    try:
        # Redirect stderr to a string buffer and also to os.devnull to suppress prints
        null_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(null_fd, 2)  # Redirect stderr (fd 2) to /dev/null
        os.close(null_fd)

        # Also redirect Python's sys.stderr
        sys.stderr = io.StringIO()

        # Run the mainloop
        root_window.mainloop()
    finally:
        # Restore stderr
        try:
            os.dup2(original_stderr_fd, 2)
            os.close(original_stderr_fd)
        except Exception:
            pass
        sys.stderr = original_stderr
