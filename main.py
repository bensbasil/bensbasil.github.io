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
            container.innerHTML = "<p class='text-gray-500 reveal delay-100'>Check back soon for new projects.</p>"
            return
            
        html = ""
        delay = 100
        for p in projects:
            title = p.get('title', 'Project')
            desc = p.get('description', '')
            tech = p.get('technologies', '')
            github = p.get('github_link', '#')
            live = p.get('live_link', '#')
            
            # Format technologies as crisp teal tags
            tech_tags = "".join([f"<span class='px-3 py-1 bg-brand-teal/10 text-brand-teal rounded-full text-[10px] uppercase tracking-widest font-bold'>{t.strip()}</span>" for t in tech.split(',') if t.strip()])
            
            html += f"""
            <div class='reveal delay-{delay} group bg-[#0f0f0f] border border-white/5 p-8 lg:p-12 rounded-[2rem] hover:-translate-y-2 hover:bg-[#161616] hover:border-white/10 transition-all duration-500 overflow-hidden relative'>
                <!-- Glow effect on hover -->
                <div class='absolute -inset-px bg-gradient-to-br from-brand-teal/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[2rem] pointer-events-none blur-xl'></div>
                
                <div class='relative z-10'>
                    <h3 class='text-3xl font-black text-white mb-6 group-hover:text-brand-teal transition-colors duration-300'>{title}</h3>
                    <p class='text-gray-400 mb-8 leading-relaxed max-w-md'>{desc}</p>
                    
                    <div class='flex flex-wrap gap-2 mb-10'>
                        {tech_tags}
                    </div>
                </div>

                <div class='relative z-10 flex gap-6 items-center'>
                    <a href='{live}' target='_blank' class='inline-flex items-center space-x-2 text-sm font-bold uppercase tracking-widest text-white hover:text-brand-teal transition-colors'>
                        <span>Live Site</span>
                        <svg class="w-4 h-4 transform group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
                    </a>
                    <a href='{github}' target='_blank' class='text-sm font-bold uppercase tracking-widest text-gray-500 hover:text-white transition-colors'>GitHub</a>
                </div>
            </div>
            """
            delay = min(delay + 100, 500)
            
        container.innerHTML = html
        
        # Trigger the intersection observer manually if defined (since these are injected late)
        window.observeElements()
        
    except Exception as e:
        print("Could not load projects:", e)
        container.innerHTML = "<p class='text-zinc-500'>Error loading projects.</p>"

# Initialize the fetching if we're on the page with projects
if document.querySelector("#projects-container"):
    asyncio.ensure_future(load_projects())
