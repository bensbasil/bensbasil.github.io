from pyscript import when, document, window
import urllib.parse
import asyncio
import json
from pyodide.http import pyfetch

# --- Contact Form Logic ---
@when("submit", "#contact-form")
def handle_contact_submit(event):
    event.preventDefault()
    
    name = document.getElementById("name").value
    email = document.getElementById("email").value
    message = document.getElementById("message").value
    
    msg_box = document.getElementById("form-message")
    msg_box.innerHTML = f"Thanks {name}! Opening your email client..."
    msg_box.className = "mb-8 p-5 rounded-2xl text-sm bg-green-50 text-green-700 block"
    msg_box.style.display = "block"
    
    subject = "Portfolio Inquiry"
    body = f"From: {name} ({email})\n\n{message}"
    mailto_url = f"mailto:bensdbasil@gmail.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    
    # Redirect to mailto link
    window.location.href = mailto_url


# --- Projects Fetching Logic ---
async def load_projects():
    container = document.querySelector("#projects-container")
    if not container:
        return
        
    try:
        response = await pyfetch("projects.json")
        projects = await response.json()
        
        if not projects:
            container.innerHTML = "<p class='text-zinc-500'>Check back soon for new projects.</p>"
            return
            
        html = ""
        for p in projects:
            title = p.get('title', 'Project')
            desc = p.get('description', '')
            tech = p.get('technologies', '')
            github = p.get('github_link', '#')
            live = p.get('live_link', '#')
            
            html += f"""
            <div class='bg-white border border-zinc-100 p-8 rounded-[2rem] hover:shadow-lg transition-all'>
                <h3 class='text-2xl font-bold text-brand-dark mb-4'>{title}</h3>
                <p class='text-zinc-500 mb-6'>{desc}</p>
                <div class='text-xs font-bold uppercase tracking-widest text-brand-green mb-8'>{tech}</div>
                <div class='flex gap-4'>
                    <a href='{live}' target='_blank' class='text-sm font-bold text-brand-dark hover:text-brand-green'>Live Site &rarr;</a>
                    <a href='{github}' target='_blank' class='text-sm font-bold text-zinc-400 hover:text-brand-dark'>GitHub</a>
                </div>
            </div>
            """
        container.innerHTML = html
        
    except Exception as e:
        print("Could not load projects:", e)
        container.innerHTML = "<p class='text-zinc-500'>Error loading projects.</p>"

# Initialize the fetching if we're on the page with projects
if document.querySelector("#projects-container"):
    asyncio.ensure_future(load_projects())
