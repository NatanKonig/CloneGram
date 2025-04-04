from tqdm import tqdm
import time
import asyncio

def create_progress_callback(desc: str = ""):
    """Create a progress callback function for Telethon's download/upload methods"""
    start_time = time.time()
    progress_bar = tqdm(
        total=100,  
        unit='B',
        unit_scale=True,
        desc=desc,
        leave=True
    )

    # Return the callback function
    def wrapped_progress_callback(received_bytes, total_bytes):
        progress = (received_bytes / total_bytes) * 100
        progress_bar.n = progress  
        progress_bar.last_print_n = progress
        progress_bar.update(0)  
        # Calculate the transfer speed to show
        progress_bar.set_postfix({
            'Speed': f"{(received_bytes / (time.time() - start_time)) / 1024 / 1024:.2f} MB/s"
        })
    
    return wrapped_progress_callback

def empty_queue(queue: asyncio.Queue):
    """Empty an asyncio Queue"""
    while not queue.empty():
        queue.get_nowait()
        queue.task_done()