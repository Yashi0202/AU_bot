// DOM Elements
const authModal = document.getElementById("authModal");
const closeModal = document.querySelectorAll(".close");
const authTitle = document.getElementById("authTitle");
const switchAuth = document.getElementById("switchAuth");
const authBtn = document.getElementById("authBtn");
const toggleAuthText = document.getElementById("toggleAuth");
const nameInput = document.getElementById("name");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const authError = document.getElementById("authError");

// New toggle buttons
const loginToggle = document.getElementById("loginToggle");
const signupToggle = document.getElementById("signupToggle");
const showPasswordCheckbox = document.getElementById("showPassword");

const dashboard = document.getElementById("dashboard");
const userNameSpan = document.getElementById("userName");
const goldWalletSpan = document.getElementById("goldWallet");
const buyGoldBtn = document.getElementById("buyGoldBtn");
const refreshBtn = document.getElementById("refreshBtn");

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const suggestionChips = document.getElementById("suggestion-chips");

const purchaseModal = document.getElementById("purchaseModal");
const goldAmountInput = document.getElementById("goldAmount");
const purchaseBtn = document.getElementById("purchaseBtn");

// API base URL - automatically detect environment
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:3000' 
    : `https://${window.location.hostname}`;

// Auth state
let isSignup = false;
let currentUser = {email:"", name:"", goldBalance:0};

// Suggestion chips data
const chipActions = {
  'help': 'I can help you with:\n• Gold investment advice\n• Digital gold purchases\n• Financial planning\n• Investment tips\n\nWhat would you like to know?',
  'buy-gold': 'Great! Let\'s get you started with digital gold investment. How much would you like to invest in ₹?',
  'investment-tips': 'Here are some smart investment tips:\n\n💡 Start small and invest regularly\n💡 Diversify your portfolio\n💡 Digital gold is safe and liquid\n💡 Consider long-term investment\n\nWould you like to know more about any specific aspect?',
  'gold-info': '🪙 **Digital Gold Benefits:**\n\n✅ Safe & Secure\n✅ 24/7 Trading\n✅ No Storage Worries\n✅ Pure 24K Gold\n✅ Instant Liquidity\n✅ Low Investment\n\nReady to start investing?'
};

// Show auth modal on page load
authModal.style.display = "flex";

// Toggle between login and signup modes
function setAuthMode(mode) {
    isSignup = mode === 'signup';
    
    if(isSignup) {
        authTitle.innerText = "Create Account";
        authBtn.innerText = "Sign Up";
        nameInput.style.display = "block";
        toggleAuthText.innerHTML = 'Already have an account? <span id="switchAuth">Login</span>';
        
        // Update toggle buttons
        loginToggle.classList.remove('active');
        signupToggle.classList.add('active');
    } else {
        authTitle.innerText = "Login";
        authBtn.innerText = "Login";
        nameInput.style.display = "none";
        toggleAuthText.innerHTML = 'Don\'t have an account? <span id="switchAuth">Create Account</span>';
        
        // Update toggle buttons
        loginToggle.classList.add('active');
        signupToggle.classList.remove('active');
    }
    
    // Re-attach event listener for switchAuth
    document.getElementById("switchAuth").addEventListener("click", () => {
        setAuthMode(isSignup ? 'login' : 'signup');
    });
}

// Toggle button event listeners
loginToggle.addEventListener("click", () => setAuthMode('login'));
signupToggle.addEventListener("click", () => setAuthMode('signup'));

// Show password functionality
showPasswordCheckbox.addEventListener("change", () => {
    passwordInput.type = showPasswordCheckbox.checked ? "text" : "password";
});

// Switch auth mode via text link
switchAuth.addEventListener("click", () => {
    setAuthMode(isSignup ? 'login' : 'signup');
});

// Close modals
closeModal.forEach(el=>el.addEventListener("click",()=>{el.parentElement.parentElement.style.display="none";}));

// Login/Signup handler
authBtn.addEventListener("click", async () => {
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();
    const name = nameInput.value.trim();

    if(!email || !password || (isSignup && !name)){
        authError.innerText = "All fields are required";
        return;
    }

    try{
        const url = isSignup ? `${API_BASE}/api/signup` : `${API_BASE}/api/login`;
        const body = isSignup ? {email,password,name} : {email,password};
        const res = await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
        const data = await res.json();
        if(res.ok){
            if(isSignup){ alert(data.message); setAuthMode('login'); return; }
            authModal.style.display = "none";
            currentUser = {email:data.email,name:data.name,goldBalance:data.goldBalance};
            userNameSpan.innerText = currentUser.name;
            goldWalletSpan.innerText = currentUser.goldBalance;
            dashboard.classList.remove("hidden");
            
            // Show welcome message with chips
            addMessage("Welcome! I'm AU Bot, your digital gold investment assistant. How can I help you today?", "bot");
            showRelevantChips("welcome");
        } else { authError.innerText = data.error; }
    } catch(err){ authError.innerText = "Server error"; console.error(err);}
});

// Add chat message with improved styling
const addMessage = (msg, sender) => {
    const div = document.createElement("div");
    div.classList.add("chat-message", sender==="user"?"user-msg":"bot-msg");
    
    // Handle line breaks for bot messages
    if (sender === "bot") {
        div.innerHTML = msg.replace(/\n/g, '<br>');
    } else {
        div.innerText = msg;
    }
    
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Show relevant suggestion chips based on context
function showRelevantChips(context) {
    const chips = suggestionChips.querySelectorAll('.chip');
    
    chips.forEach(chip => {
        const action = chip.dataset.action;
        
        switch(context) {
            case 'welcome':
                chip.style.display = 'inline-block';
                break;
            case 'gold-interest':
                if (action === 'buy-gold' || action === 'gold-info') {
                    chip.style.display = 'inline-block';
                } else {
                    chip.style.display = 'none';
                }
                break;
            case 'investment-interest':
                if (action === 'investment-tips' || action === 'buy-gold') {
                    chip.style.display = 'inline-block';
                } else {
                    chip.style.display = 'none';
                }
                break;
            default:
                chip.style.display = 'inline-block';
        }
    });
}

// Handle suggestion chip clicks
suggestionChips.addEventListener('click', (e) => {
    if (e.target.classList.contains('chip')) {
        const action = e.target.dataset.action;
        const message = chipActions[action];
        
        if (message) {
            addMessage(message, 'bot');
            
            // Show relevant follow-up chips
            if (action === 'buy-gold') {
                showRelevantChips('gold-interest');
                // Auto-open purchase modal
                setTimeout(() => {
                    purchaseModal.style.display = "flex";
                }, 1000);
            } else if (action === 'investment-tips') {
                showRelevantChips('investment-interest');
            }
        }
    }
});

// Send query with improved keyword detection
const sendQuery = async (query)=>{
    if(!query) return;
    addMessage(query,"user");
    
    // Analyze query for chip suggestions
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('gold') || lowerQuery.includes('buy') || lowerQuery.includes('invest')) {
        showRelevantChips('gold-interest');
    } else if (lowerQuery.includes('tip') || lowerQuery.includes('advice') || lowerQuery.includes('help')) {
        showRelevantChips('investment-interest');
    }
    
    try{
        const res = await fetch(`${API_BASE}/api/query`,{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({email:currentUser.email,userQuery:query})
        });
        const data = await res.json();
        if(data.redirectToPurchase){ 
            addMessage(data.message,"bot"); 
            purchaseModal.style.display="flex";
            showRelevantChips('gold-interest');
        }
        else addMessage(data.message,"bot");
    }catch(err){ addMessage("⚠️ Server error","bot"); console.error(err);}
}

// Purchase gold
const purchaseGold = async ()=>{
    const amount = parseFloat(goldAmountInput.value);
    if(!amount || amount<=0) return alert("Enter a valid amount");
    try{
        const res = await fetch(`${API_BASE}/api/purchase-gold`,{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({email:currentUser.email,amount})
        });
        const data = await res.json();
        addMessage(`✅ ${data.message}`,"bot");
        currentUser.goldBalance = data.updatedGoldBalance;
        goldWalletSpan.innerText = currentUser.goldBalance;
        goldAmountInput.value = "";
        purchaseModal.style.display="none";
        
        // Show success chips
        showRelevantChips('gold-interest');
    }catch(err){ addMessage("⚠️ Purchase failed","bot"); console.error(err);}
}

// Event listeners
sendBtn.addEventListener("click",()=>{sendQuery(userInput.value.trim()); userInput.value="";});
userInput.addEventListener("keypress", e=>{if(e.key==="Enter") sendBtn.click();});
purchaseBtn.addEventListener("click", purchaseGold);
buyGoldBtn?.addEventListener("click", ()=>{ purchaseModal.style.display = "flex"; });
refreshBtn?.addEventListener("click", async ()=>{
    if(!currentUser.email) return;
    try{
        const res = await fetch(`${API_BASE}/api/user?email=${encodeURIComponent(currentUser.email)}`);
        const data = await res.json();
        if(data && data.goldBalance!==undefined){
            currentUser.goldBalance = data.goldBalance;
            goldWalletSpan.innerText = currentUser.goldBalance;
        }
    }catch(e){ console.error(e); }
});

// Dynamic grams update
goldAmountInput.addEventListener("input",()=>{
    const amount = parseFloat(goldAmountInput.value);
    if(!amount) return;
    fetch(`${API_BASE}/api/gold-price`).then(res=>res.json()).then(data=>{
        const grams = (amount/data.pricePerGram).toFixed(5);
        document.querySelector(".modal-content h3").innerText=`💎 Purchase Digital Gold - ${grams} g`;
    });
});
