class VideoGenerator {
    constructor() {
        this.currentSessionId = null;
        this.pollInterval = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Form submission
        document.getElementById('videoForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startGeneration();
        });

        // Download video button
        document.getElementById('downloadVideoBtn').addEventListener('click', () => {
            this.downloadVideo();
        });

        // View assets button
        document.getElementById('viewAssetsBtn').addEventListener('click', () => {
            this.viewAssets();
        });

        // Start over button
        document.getElementById('startOverBtn').addEventListener('click', () => {
            this.startOver();
        });

        // Retry button
        document.getElementById('retryBtn').addEventListener('click', () => {
            this.startGeneration();
        });
    }

    async startGeneration() {
        const topic = document.getElementById('topicInput').value.trim();
        
        if (!topic) {
            this.showError('Please enter a historical topic.');
            return;
        }

        try {
            // Show progress section
            this.showProgressSection();
            this.resetProgress();

            // Start generation
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic: topic })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.currentSessionId = data.session_id;

            // Start polling for status
            this.startPolling();

        } catch (error) {
            console.error('Error starting generation:', error);
            this.showError(`Failed to start generation: ${error.message}`);
        }
    }

    showProgressSection() {
        // Hide other sections
        document.getElementById('resultsCard').classList.add('d-none');
        document.getElementById('errorCard').classList.add('d-none');
        
        // Show progress section
        document.getElementById('progressCard').classList.remove('d-none');
        document.getElementById('progressCard').classList.add('fade-in');
        
        // Disable generate button
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Generating...';
    }

    resetProgress() {
        // Reset progress bar
        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = '0%';
        progressBar.textContent = '0%';
        progressBar.setAttribute('aria-valuenow', '0');

        // Reset step indicators
        const steps = ['script', 'images', 'voiceover', 'video'];
        steps.forEach(step => {
            const element = document.getElementById(`step-${step}`);
            element.classList.remove('active', 'completed');
        });

        // Reset message
        document.getElementById('progressMessage').textContent = 'Initializing...';
    }

    startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.currentSessionId}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const status = await response.json();
                this.updateProgress(status);

                if (status.status === 'completed') {
                    this.stopPolling();
                    this.showResults();
                } else if (status.status === 'error') {
                    this.stopPolling();
                    this.showError(status.message);
                }

            } catch (error) {
                console.error('Error polling status:', error);
                this.stopPolling();
                this.showError('Failed to check generation status');
            }
        }, 2000); // Poll every 2 seconds
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    updateProgress(status) {
        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        progressBar.style.width = `${status.progress}%`;
        progressBar.textContent = `${status.progress}%`;
        progressBar.setAttribute('aria-valuenow', status.progress);

        // Update message
        document.getElementById('progressMessage').textContent = status.message;

        // Update step indicators
        this.updateStepIndicators(status.status, status.progress);
    }

    updateStepIndicators(status, progress) {
        const steps = [
            { name: 'script', threshold: 10 },
            { name: 'images', threshold: 30 },
            { name: 'voiceover', threshold: 70 },
            { name: 'video', threshold: 85 }
        ];
        
        // Handle special overlay status
        if (status === 'adding_overlays') {
            const imagesStep = document.getElementById('step-images');
            if (imagesStep) {
                imagesStep.classList.add('active');
                imagesStep.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Adding text overlays...';
            }
            return;
        }

        steps.forEach(step => {
            const element = document.getElementById(`step-${step.name}`);
            
            if (status.includes(step.name) || progress >= step.threshold) {
                element.classList.add('active');
                element.classList.remove('completed');
            }
            
            if (progress > step.threshold) {
                element.classList.remove('active');
                element.classList.add('completed');
            }
        });
    }

    async showResults() {
        // Hide progress section
        document.getElementById('progressCard').classList.add('d-none');
        
        // Show results section
        document.getElementById('resultsCard').classList.remove('d-none');
        document.getElementById('resultsCard').classList.add('fade-in');
        
        // Reset generate button
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-play me-2"></i>Generate Video';

        // Set video source for preview
        const videoPlayer = document.getElementById('videoPlayer');
        videoPlayer.src = `/download/${this.currentSessionId}`;
    }

    async downloadVideo() {
        if (!this.currentSessionId) {
            this.showError('No video available for download');
            return;
        }

        try {
            const link = document.createElement('a');
            link.href = `/download/${this.currentSessionId}`;
            link.download = `history_${this.currentSessionId}.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error downloading video:', error);
            this.showError('Failed to download video');
        }
    }

    async viewAssets() {
        if (!this.currentSessionId) {
            this.showError('No assets available');
            return;
        }

        try {
            const response = await fetch(`/assets/${this.currentSessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const assets = await response.json();
            this.displayAssetsModal(assets);

        } catch (error) {
            console.error('Error fetching assets:', error);
            this.showError('Failed to load assets');
        }
    }

    displayAssetsModal(assets) {
        const modalBody = document.getElementById('assetsModalBody');
        
        let html = '';

        // Script
        if (assets.script) {
            html += `
                <div class="asset-item">
                    <h6><i class="fas fa-file-alt me-2"></i>Script</h6>
                    <div class="bg-light p-3 rounded mb-2" style="max-height: 200px; overflow-y: auto;">
                        <pre style="white-space: pre-wrap; margin: 0;">${assets.script}</pre>
                    </div>
                </div>
            `;
        }

        // Images
        if (assets.images && assets.images.length > 0) {
            html += `
                <div class="asset-item">
                    <h6><i class="fas fa-images me-2"></i>Generated Images (${assets.images.length})</h6>
                    <div class="row">
            `;
            
            assets.images.forEach((imageUrl, index) => {
                html += `
                    <div class="col-md-4 mb-3">
                        <img src="${imageUrl}" class="img-fluid rounded" alt="Generated image ${index + 1}">
                        <div class="text-center mt-2">
                            <a href="${imageUrl}" class="btn btn-sm btn-outline-primary" download>
                                <i class="fas fa-download me-1"></i>Download
                            </a>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }

        // Voiceover
        if (assets.voiceover) {
            html += `
                <div class="asset-item">
                    <h6><i class="fas fa-microphone me-2"></i>Voiceover</h6>
                    <audio controls class="w-100 mb-2">
                        <source src="${assets.voiceover}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                    <a href="${assets.voiceover}" class="btn btn-sm btn-outline-primary" download>
                        <i class="fas fa-download me-1"></i>Download Audio
                    </a>
                </div>
            `;
        }

        // Video
        if (assets.video) {
            html += `
                <div class="asset-item">
                    <h6><i class="fas fa-video me-2"></i>Final Video</h6>
                    <a href="${assets.video}" class="btn btn-success">
                        <i class="fas fa-download me-1"></i>Download Video
                    </a>
                </div>
            `;
        }

        modalBody.innerHTML = html;

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('assetsModal'));
        modal.show();
    }

    startOver() {
        // Reset everything
        this.currentSessionId = null;
        this.stopPolling();
        
        // Hide all sections except the main form
        document.getElementById('progressCard').classList.add('d-none');
        document.getElementById('resultsCard').classList.add('d-none');
        document.getElementById('errorCard').classList.add('d-none');
        
        // Reset form
        document.getElementById('topicInput').value = '';
        document.getElementById('topicInput').focus();
        
        // Reset generate button
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-play me-2"></i>Generate Video';
    }

    showError(message) {
        // Stop polling
        this.stopPolling();
        
        // Hide other sections
        document.getElementById('progressCard').classList.add('d-none');
        document.getElementById('resultsCard').classList.add('d-none');
        
        // Show error section
        document.getElementById('errorCard').classList.remove('d-none');
        document.getElementById('errorCard').classList.add('fade-in');
        document.getElementById('errorMessage').textContent = message;
        
        // Reset generate button
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-play me-2"></i>Generate Video';
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new VideoGenerator();
});

// Add some visual enhancements
document.addEventListener('DOMContentLoaded', () => {
    // Add scanline effect to cards
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach(card => {
        card.classList.add('scanline-overlay');
    });

    // Add glitch effect to the title on hover
    const title = document.querySelector('.navbar-brand');
    if (title) {
        title.addEventListener('mouseenter', () => {
            title.classList.add('glitch');
            setTimeout(() => {
                title.classList.remove('glitch');
            }, 1000);
        });
    }
});

// Social sharing functions
function shareOnFacebook() {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent("Check out this amazing AI-powered historical video generator!");
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${title}`;
    window.open(facebookUrl, '_blank', 'width=600,height=400');
}

function shareOnTwitter() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent("Create amazing historical videos with AI! Check out RunHistory.log Generator 🎬📚");
    const twitterUrl = `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
    window.open(twitterUrl, '_blank', 'width=600,height=400');
}

function copyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
        // Show success message
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.innerHTML = '✅ Link copied to clipboard!';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 15px 20px;
            border-radius: 5px;
            z-index: 1000;
            font-weight: bold;
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = window.location.href;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        alert('Link copied to clipboard!');
    });
}
