from pyscript import when, document, window
import urllib.parse
import asyncio
import json
from pyodide.http import pyfetch

# --- Contact Form Logic ---
@when("submit", "#contact-form")
async def handle_contact_submit(event):
    event.preventDefault()
    
    name = document.getElementById("name").value
    email = document.getElementById("email").value
    message = document.getElementById("message").value
    
    msg_box = document.getElementById("form-message")
    msg_box.innerHTML = "Sending message..."
    msg_box.className = "mb-8 p-5 rounded-2xl text-sm border border-blue-200 bg-blue-50 text-blue-700 block"
    msg_box.style.display = "block"
    
    try:
        response = await pyfetch(
            "https://api.bensbasil.in/contact",
            method="POST",
            headers={
                "Content-Type": "application/json"
            },
            body=json.dumps({
                "name": name,
                "email": email,
                "message": message
            })
        )
        if response.ok:
            msg_box.innerHTML = f"Thanks {name}! Your message has been securely submitted."
            msg_box.className = "mb-8 p-5 rounded-2xl text-sm border border-green-200 bg-green-50 text-green-700 block"
            document.getElementById("contact-form").reset()
        else:
            msg_box.innerHTML = "Failed to send message. Please try again."
            msg_box.className = "mb-8 p-5 rounded-2xl text-sm border border-red-200 bg-red-50 text-red-700 block"
    except Exception as e:
        msg_box.innerHTML = f"Network Error: Could not connect to the backend server."
        msg_box.className = "mb-8 p-5 rounded-2xl text-sm border border-red-200 bg-red-50 text-red-700 block"


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
            
        html = """
        <a href='./quiz/'
        class='group relative bg-white rounded-2xl border border-black/10 overflow-hidden hover:-translate-y-1 transition-transform duration-200 block no-underline'>
        <div class='p-8 flex items-start gap-5'>
            <div class='w-[72px] h-[72px] rounded-2xl bg-brand-dark flex-shrink-0 overflow-hidden border border-black/10'>
                <img src='./quiz/icon.png' alt='Quiz app icon' class='w-full h-full object-cover' />
            </div>
            <div class='flex-1 min-w-0'>
                <p class='text-xs font-bold tracking-widest uppercase text-gray-400 mb-1'>Quiz App</p>
                <h3 class='text-2xl font-black text-brand-dark tracking-tighter leading-tight mb-1'>The Knowledge Quiz</h3>
                <p class='text-sm text-gray-500 leading-relaxed'>Test your knowledge with timed rounds, score tracking, and instant feedback.</p>
            </div>
        </div>
        <div class='mx-8 border-t border-black/[0.06]'></div>
        <div class='px-8 py-4 flex items-center justify-between'>
            <div class='flex gap-2'>
                <span class='text-xs font-medium bg-brand-green/10 text-brand-green px-3 py-1 rounded-full'>JavaScript</span>
                <span class='text-xs font-medium bg-black/5 text-gray-500 px-3 py-1 rounded-full'>HTML/CSS</span>
            </div>
            <span class='text-sm font-bold text-brand-dark flex items-center gap-1'>
                Play
                <svg class='w-4 h-4' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                    <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2.5' d='M17 8l4 4m0 0l-4 4m4-4H3'/>
                </svg>
            </span>
        </div>
    </a>
    """
        delay = 100
        for p in projects:
            title = p.get('title', 'Project')
            desc = p.get('description', '')
            tech = p.get('technologies', '')
            github = p.get('github_link', '#')
            live = p.get('live_link', '#')
            
            # Format technologies as crisp teal tags
            tech_tags = "".join([f"<span class='px-3 py-1 bg-white border border-black/5 text-gray-500 rounded-full text-xs font-semibold'>{t.strip()}</span>" for t in tech.split(',') if t.strip()])
            
            html += f"""
            <div class='reveal delay-{delay} group bg-[#F9F9F9] p-8 lg:p-12 rounded-[2rem] hover:bg-white transition-colors duration-300 relative'>
                <!-- Top Right Simple Arrow -->
                <div class='absolute top-8 right-8 text-gray-300 group-hover:text-brand-green transform group-hover:-rotate-45 transition-all duration-300'>
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </div>

                <div class='relative z-10'>
                    <h3 class='text-3xl font-bold text-brand-dark mb-4'>{title}</h3>
                    <p class='text-gray-500 mb-8 leading-relaxed max-w-md font-medium text-lg'>{desc}</p>
                    
                    <div class='flex flex-wrap gap-2 mb-10'>
                        {tech_tags}
                    </div>
                </div>

                <div class='relative z-10 flex gap-6 items-center'>
                    <a href='{live}' target='_blank' class='inline-flex items-center space-x-2 font-bold text-brand-dark hover:text-brand-green transition-colors'>
                        <span>View Project</span>
                    </a>
                    <a href='{github}' target='_blank' class='font-bold text-gray-400 hover:text-brand-dark transition-colors'>GitHub source</a>
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