# GitHub Webhook Monitor

A Flask application that receives GitHub webhooks and displays repository activity in real-time.

## Features

- Receives GitHub webhooks for push, pull request, and merge events
- Stores activity data in MongoDB
- Real-time UI that polls for updates every 15 seconds
- Clean, responsive design
- RESTful API endpoints

## Setup Instructions

### Prerequisites

- Python 3.7+
- MongoDB instance
- GitHub repository with webhook access

### Installation

1. Clone the repository:
```bash
git clone <webhook-repo-url>
cd webhook-repo