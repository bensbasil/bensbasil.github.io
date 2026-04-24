#!/bin/bash

# Update and install system dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx postgresql python3-pip python3-venv nodejs npm certbot python3-certbot-nginx

# Install PM2 globally
sudo npm install -g pm2

# Create web root and set permissions
sudo mkdir -p /var/www/portfolio
sudo chown -R $USER:$USER /var/www/portfolio

# Note: You should clone your repository into a folder in your home directory
# and then copy/link the frontend files to /var/www/portfolio

echo "System dependencies installed."
echo "Next steps:"
echo "1. Clone your repo: git clone <your-repo-url>"
echo "2. Copy frontend files: cp -r ./Portfolio_Website/* /var/www/portfolio/"
echo "3. Setup .env files in backend/"
echo "4. Create venv and install requirements: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "5. Copy nginx config: sudo cp ./deployment/nginx.conf /etc/nginx/sites-available/portfolio"
echo "6. Enable site: sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/"
echo "7. Restart nginx: sudo systemctl restart nginx"
echo "8. Start backends: pm2 start ./deployment/ecosystem.config.js"
echo "9. Run certbot: sudo certbot --nginx"
