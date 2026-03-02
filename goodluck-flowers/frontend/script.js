const API_URL = 'http://localhost:8000';
let currentUser = null;
let currentProductForPurchase = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    checkSession();
});

async function loadProducts() {
    try {
        const response = await fetch(`${API_URL}/api/products`);
        const data = await response.json();
        
        const grid = document.getElementById('productsGrid');
        grid.innerHTML = data.products.map(product => {
            const encodedName = encodeURIComponent(product.name);
            const imageUrl = product.image_url.startsWith('http') ? product.image_url : `${API_URL}${product.image_url}`;
            return `
            <div class="product-card">
                <img src="${imageUrl}" alt="${product.name}" class="product-image"
                    onload="this.classList.add('loaded')"
                    onerror="this.onerror=null; this.src='https://via.placeholder.com/400x250?text=${encodedName}'; this.classList.add('loaded');">
                <div class="product-info">
                    <div class="product-name">${product.name}</div>
                    <div class="product-description">${product.description}</div>
                    <div class="product-price">$${product.price}</div>
                    <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">Stock: ${product.stock}</div>
                    <button class="buy-btn" onclick="buyProduct(${product.id})">Buy Now</button>
                    <button class="comments-toggle" onclick="toggleComments(${product.id})">💬 Comments</button>
                    
                    <div class="comments-section" id="comments-${product.id}">
                        <div class="comments-list" id="comments-list-${product.id}">
                            <div style="text-align: center; color: #999; padding: 1rem;">Loading comments...</div>
                        </div>
                        <div class="comment-form">
                            <input type="text" placeholder="Your name" id="author-${product.id}" class="comment-author-input">
                            <textarea placeholder="Write a comment..." id="comment-text-${product.id}" class="comment-text-input"></textarea>
                            <button onclick="submitComment(${product.id})">Post Comment</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        }).join('');
        
        console.log('✅ Products loaded from backend');
    } catch (error) {
        console.error('❌ Error loading products:', error);
        document.getElementById('productsGrid').innerHTML = `
            <div class="alert alert-danger">
                Failed to load products. Make sure the backend server is running on port 8000.
                <br><br>
                Run: <code>cd backend && python main.py</code>
            </div>
        `;
    }
}

function checkSession() {
    const user = localStorage.getItem('user');
    if (user) {
        try {
            currentUser = JSON.parse(user);
            if (currentUser.role === 'admin' || currentUser.role === 'superadmin') {
                document.getElementById('adminBtn').style.display = 'block';
            }
            document.getElementById('logoutBtn').style.display = 'block';
            console.log('✅ User session restored:', currentUser);
        } catch (e) {
            console.error('Error parsing user session:', e);
        }
    }
}

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch(`${API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        console.log('🔐 Login response:', data);
        
        if (data.success) {
            // VULNERABILITY: Store sensitive data in localStorage
            localStorage.setItem('user', JSON.stringify(data.user));
            currentUser = data.user;
            
            showMessage('loginMessage', '✅ Login successful!', 'success');
            
            if (data.user.role === 'admin' || data.user.role === 'superadmin') {
                document.getElementById('adminBtn').style.display = 'block';
                console.log('🎉 ADMIN ACCESS GRANTED!');
            }
            
            document.getElementById('logoutBtn').style.display = 'block';
            
            // Show SQL injection success
            if (data.debug_query && (data.debug_query.includes("OR '1'='1'") || data.debug_query.includes("OR 1=1"))) {
                console.log('🚨 SQL INJECTION SUCCESSFUL!');
                console.log('Executed query:', data.debug_query);
                showMessage('loginMessage', '🎉 SQL INJECTION SUCCESSFUL! Check console for query.', 'success');
            }
            
            setTimeout(() => closeModal('loginModal'), 2000);
        } else {
            showMessage('loginMessage', '❌ ' + data.message, 'danger');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('loginMessage', '❌ Connection error. Is the backend running?', 'danger');
    }
}

function logout() {
    localStorage.removeItem('user');
    currentUser = null;
    document.getElementById('adminBtn').style.display = 'none';
    document.getElementById('logoutBtn').style.display = 'none';
    document.getElementById('adminPanel').classList.add('hidden');
    console.log('👋 Logged out');
}

function buyProduct(productId) {
    fetch(`${API_URL}/api/products`)
        .then(r => r.json())
        .then(data => {
            const product = data.products.find(p => p.id === productId);
            if (product) {
                currentProductForPurchase = product;
                document.getElementById('purchaseProductInfo').innerHTML = `
                    <div style="background: #f5f5f5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                        <h3>${product.name}</h3>
                        <p>Price: $${product.price}</p>
                    </div>
                `;
                document.getElementById('purchaseModal').style.display = 'block';
            }
        });
}

async function completePurchase() {
    if (!currentProductForPurchase) return;
    
    const creditCard = document.getElementById('creditCard').value;
    const cvv = document.getElementById('cvv').value;
    const quantity = parseInt(document.getElementById('quantity').value);
    
    if (!creditCard || !cvv) {
        showMessage('purchaseMessage', '❌ Please fill all fields', 'danger');
        return;
    }
    
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (currentUser && currentUser.token) {
            headers['Authorization'] = `Bearer ${currentUser.token}`;
        }
        
        const response = await fetch(`${API_URL}/api/orders`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                product_id: currentProductForPurchase.id,
                quantity: quantity,
                credit_card: creditCard,
                cvv: cvv
            })
        });
        
        const data = await response.json();
        console.log('💳 Purchase response:', data);
        console.log('🚨 VULNERABILITY: Credit card data exposed in response!');
        
        if (data.success) {
            showMessage('purchaseMessage', '✅ Purchase successful! Check console for details.', 'success');
            setTimeout(() => {
                closeModal('purchaseModal');
                alert(`Thank you for purchasing ${currentProductForPurchase.name}! Total: $${data.total_price}`);
            }, 2000);
        }
    } catch (error) {
        console.error('Purchase error:', error);
        showMessage('purchaseMessage', '❌ Purchase failed', 'danger');
    }
}

async function sendAIMessage() {
    const input = document.getElementById('aiInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const messagesDiv = document.getElementById('aiMessages');
    
    // VULNERABILITY: XSS - displaying user input without sanitization
    messagesDiv.innerHTML += `<div class="message user">${message}</div>`;
    input.value = '';
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Show loading
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message bot';
    loadingMsg.textContent = 'Thinking...';
    messagesDiv.appendChild(loadingMsg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
        const response = await fetch(`${API_URL}/api/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        console.log('🤖 AI response:', data);
        
        messagesDiv.removeChild(loadingMsg);
        
        if (data.vulnerability_exploited) {
            console.log('🚨 VULNERABILITY EXPLOITED:', data.vulnerability_exploited);
        }
        
        // VULNERABILITY: XSS - bot response not sanitized
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot';
        botMsg.innerHTML = data.response || data.error;
        messagesDiv.appendChild(botMsg);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
    } catch (error) {
        messagesDiv.removeChild(loadingMsg);
        messagesDiv.innerHTML += `<div class="message bot">Error: ${error.message}. Make sure backend is running and you have set ANTHROPIC_API_KEY environment variable.</div>`;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

function toggleAI() {
    const ai = document.getElementById('aiAssistant');
    ai.style.display = ai.style.display === 'flex' ? 'none' : 'flex';
}

function showAdminPanel() {
    const panel = document.getElementById('adminPanel');
    panel.classList.toggle('hidden');
}

async function addFlower() {
    const name = document.getElementById('adminFlowerName').value;
    const description = document.getElementById('adminFlowerDesc').value;
    const price = parseFloat(document.getElementById('adminFlowerPrice').value);
    const image_url = document.getElementById('adminFlowerImage').value;
    const stock = parseInt(document.getElementById('adminFlowerStock').value);
    
    if (!name || !description || !price || !image_url) {
        showMessage('adminMessage', '❌ Please fill all fields', 'danger');
        return;
    }
    
    try {
        // VULNERABILITY: Weak API key that can be guessed
        const response = await fetch(`${API_URL}/api/admin/products`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'admin_api_key_xyz789'  // VULNERABILITY: Hardcoded API key
            },
            body: JSON.stringify({ name, description, price, image_url, stock })
        });
        
        const data = await response.json();
        console.log('✅ Product added:', data);
        
        if (data.success) {
            showMessage('adminMessage', '✅ Flower added successfully!', 'success');
            loadProducts();
            
            // Clear inputs
            document.getElementById('adminFlowerName').value = '';
            document.getElementById('adminFlowerDesc').value = '';
            document.getElementById('adminFlowerPrice').value = '';
            document.getElementById('adminFlowerImage').value = '';
            document.getElementById('adminFlowerStock').value = '100';
        }
    } catch (error) {
        console.error('Error adding flower:', error);
        showMessage('adminMessage', '❌ Error adding flower', 'danger');
    }
}

async function viewAllOrders() {
    try {
        const response = await fetch(`${API_URL}/api/orders`);
        const data = await response.json();
        
        console.log('🚨 VULNERABILITY: All orders exposed!');
        console.log('📊 Orders with credit card data:', data);
        
        alert('Check console to see ALL orders including credit card numbers! 🚨');
    } catch (error) {
        console.error('Error fetching orders:', error);
    }
}

async function viewAllUsers() {
    try {
        const response = await fetch(`${API_URL}/api/users`);
        const data = await response.json();
        
        console.log('🚨 VULNERABILITY: All users exposed!');
        console.log('👥 Users with passwords:', data);
        
        alert('Check console to see ALL users including passwords! 🚨');
    } catch (error) {
        console.error('Error fetching users:', error);
    }
}

function showLogin() {
    document.getElementById('loginModal').style.display = 'block';
}

function showHelp() {
    document.getElementById('helpModal').style.display = 'block';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => {
        element.innerHTML = '';
    }, 5000);
}

// Comments Functions (VULNERABILITY: XSS in comment display)
async function toggleComments(productId) {
    const section = document.getElementById(`comments-${productId}`);
    section.classList.toggle('show');
    
    if (section.classList.contains('show')) {
        loadComments(productId);
    }
}

async function loadComments(productId) {
    try {
        const response = await fetch(`${API_URL}/api/products/${productId}/comments`);
        const data = await response.json();
        const container = document.getElementById(`comments-list-${productId}`);
        
        if (data.comments.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: #999; padding: 1rem;">No comments yet. Be the first!</div>';
            return;
        }
        
        // VULNERABILITY: Using innerHTML with unsanitized comment text - allows XSS
        container.innerHTML = data.comments.map(comment => `
            <div class="comment-item">
                <div class="comment-author">${comment.author_name}</div>
                <div class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</div>
                <div class="comment-text">${comment.comment_text}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading comments:', error);
        document.getElementById(`comments-list-${productId}`).innerHTML = '<div style="color: #d00; padding: 1rem;">Error loading comments</div>';
    }
}

async function submitComment(productId) {
    const authorInput = document.getElementById(`author-${productId}`);
    const commentInput = document.getElementById(`comment-text-${productId}`);
    
    const author = authorInput.value.trim();
    const text = commentInput.value.trim();
    
    if (!author || !text) {
        alert('Please enter your name and a comment');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/products/${productId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                author_name: author,
                comment_text: text
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Comment posted successfully');
            // VULNERABILITY: Vulnerable to XSS - comment echo not sanitized
            console.log('💬 Your comment contains:', text);
            
            // Clear inputs
            authorInput.value = '';
            commentInput.value = '';
            
            // Reload comments
            loadComments(productId);
        } else {
            alert('Error posting comment');
        }
    } catch (error) {
        console.error('Error posting comment:', error);
        alert('Error posting comment. Check console for details.');
    }
}

// Log helpful info
console.log('🌸 GoodLuck Flowers - Security Challenge');
console.log('🎯 Backend API:', API_URL);
console.log('💡 Try SQL injection, access /api/users, check /api/debug/config');
console.log('🔍 Use Help button for more clues!');
console.log('📚 API Docs: http://localhost:8000/docs');
