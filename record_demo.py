import os
import sys
import asyncio
from playwright.async_api import async_playwright
from moviepy import VideoFileClip, AudioFileClip, afx

APP_URL = "https://opsguard-frontend-1092338127156.us-east1.run.app"
RECORDINGS_DIR = "/config/Desktop/Session1/opsguard-agent/raw_recordings"

async def record_playwright():
    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=RECORDINGS_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        print("1. Opening OpsGuard AI Frontend...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        print("2. Clicking 'Active Incidents' prompt chip...")
        chip1 = page.locator(".prompt-btn", has_text="Active Incidents")
        await chip1.click()
        await page.wait_for_timeout(4500)
        
        print("3. Clicking 'Topology Diagram' prompt chip...")
        chip3 = page.locator(".prompt-btn", has_text="Topology Diagram")
        await chip3.click()
        await page.wait_for_timeout(5500)
        
        print("4. Demonstrating Lightbox Modal...")
        imgs = page.locator(".a2img")
        if await imgs.count() > 0:
            await imgs.first.click()
            await page.wait_for_timeout(2500)
            await page.locator("#lightboxModal").click()
            await page.wait_for_timeout(1500)
            
        print("5. Toggling Light/Dark theme...")
        await page.click("#themeBtn")
        await page.wait_for_timeout(2500)
        
        print("Saving raw video recording...")
        video_path = await page.video.path()
        await page.close()
        await context.close()
        await browser.close()
        return video_path

def combine_audio_video(video_path, audio_path, output_mp4):
    print(f"Processing demo video from {video_path} with upbeat lo-fi audio...")
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    
    # Loop audio to match video duration
    looped_audio = afx.AudioLoop(audio_clip, duration=video_clip.duration)
    final_clip = video_clip.with_audio(looped_audio)
    
    final_clip.write_videofile(output_mp4, fps=24, codec="libx264", audio_codec="aac")
    print(f"Demo video successfully generated at: {output_mp4}")

if __name__ == "__main__":
    raw_video = asyncio.run(record_playwright())
    print("Raw video file recorded:", raw_video)
    combine_audio_video(raw_video, "lofi_track.wav", "opsguard_demo.mp4")
