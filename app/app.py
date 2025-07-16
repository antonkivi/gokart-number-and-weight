import cv2
import pytesseract
import asyncio
import websockets
import json
import threading
import time
import re
from datetime import datetime
import numpy as np

class NumberDetector:
    def __init__(self, port=8000):
        self.port = port
        self.cap = None
        self.running = False
        self.last_number = None
        self.confidence_threshold = 50
        self.connected_clients = set()
        
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.connected_clients)}")
        
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.connected_clients.discard(websocket)
        print(f"Client disconnected. Total clients: {len(self.connected_clients)}")
        
    async def broadcast_number(self, number):
        """Broadcast detected number to all connected clients"""
        if self.connected_clients:
            data = {
                "type": "number_detected",
                "number": number,
                "timestamp": datetime.now().isoformat()
            }
            message = json.dumps(data)
            
            # Send to all connected clients
            disconnected = set()
            for client in self.connected_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Remove disconnected clients
            for client in disconnected:
                self.connected_clients.discard(client)
            
            print(f"Broadcasted number {number} to {len(self.connected_clients)} clients")
        
    async def handle_client(self, websocket, path):
        """Handle new WebSocket client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                # Handle any messages from client if needed
                print(f"Received from client: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    def send_number_sync(self, number):
        """Synchronous wrapper to send number from detection thread"""
        if self.connected_clients:
            # Use thread-safe way to schedule coroutine
            def run_broadcast():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.broadcast_number(number))
                finally:
                    loop.close()
            
            # Run in a separate thread to avoid blocking
            broadcast_thread = threading.Thread(target=run_broadcast)
            broadcast_thread.daemon = True
            broadcast_thread.start()
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_numbers(self, image):
        """Extract numbers from image using OCR"""
        try:
            # Preprocess the image
            processed = self.preprocess_image(image)
            
            # OCR configuration for better number detection
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
            
            # Extract text with confidence scores
            data = pytesseract.image_to_data(processed, config=config, output_type=pytesseract.Output.DICT)
            
            numbers = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if text and conf > self.confidence_threshold:
                    # Use regex to find numbers (including decimals)
                    number_matches = re.findall(r'\d+\.?\d*', text)
                    for match in number_matches:
                        try:
                            # Convert to float if it contains decimal, otherwise int
                            if '.' in match:
                                num = float(match)
                            else:
                                num = int(match)
                            numbers.append(num)
                        except ValueError:
                            continue
            
            return numbers
            
        except Exception as e:
            print(f"OCR error: {e}")
            return []
    
    def start_detection(self):
        """Start the number detection process"""
        print("Starting number detection...")
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera")
            return
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.running = True
        frame_count = 0
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
                # Process every 5th frame to reduce CPU usage
                if frame_count % 5 == 0:
                    numbers = self.extract_numbers(frame)
                    
                    if numbers:
                        # Send the first detected number
                        current_number = numbers[0]
                        
                        # Only send if it's different from the last number
                        if current_number != self.last_number:
                            self.send_number_sync(current_number)
                            self.last_number = current_number
                
                # Display the frame (optional, comment out for headless operation)
                cv2.imshow('Number Detection', frame)
                
                # Break on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                frame_count += 1
                
        except KeyboardInterrupt:
            print("Detection stopped by user")
        finally:
            self.cleanup()
    
    async def start_websocket_server(self):
        """Start the WebSocket server"""
        print(f"Starting WebSocket server on ws://localhost:{self.port}")
        async with websockets.serve(self.handle_client, "localhost", self.port):
            await asyncio.Future()  # Run forever
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Cleanup completed")

async def main():
    # Configuration
    PORT = 8000  # WebSocket server port
    
    detector = NumberDetector(PORT)
    
    # Start WebSocket server in background
    server_task = asyncio.create_task(detector.start_websocket_server())
    
    # Start detection in a separate thread
    detection_thread = threading.Thread(target=detector.start_detection)
    detection_thread.daemon = True
    detection_thread.start()
    
    try:
        # Keep the server running
        await server_task
    except KeyboardInterrupt:
        print("Server stopped by user")
    finally:
        detector.cleanup()

if __name__ == "__main__":
    asyncio.run(main())