const CART_COOKIE_NAME = 'echoshop_cart';

function getCart() {
    try {
        return JSON.parse(localStorage.getItem('cart') || '{}');
    } catch (e) {
        return {};
    }
}

function saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add to notification container or create it if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function addToCart(productId) {
    const cart = getCart();
    cart[productId] = (cart[productId] || 0) + 1;
    saveCart(cart);
    showNotification('Produkt byl přidán do košíku');
}

function removeFromCart(productId) {
    const cart = getCart();
    delete cart[productId];
    saveCart(cart);
    
    // Check if we're on the cart page and handle display
    if (window.location.pathname === '/cart') {
        const items = Object.keys(cart);
        const cartEmpty = document.getElementById('cart-empty');
        const cartContent = document.getElementById('cart-content');
        
        if (items.length === 0) {
            cartContent.style.display = 'none';
            cartEmpty.style.display = 'block';
        } else {
            loadCart(); // Refresh the cart display
        }
    }
    
    showNotification('Produkt byl odebrán z košíku', 'warning');
}

function updateQuantity(productId, quantity) {
    const cart = getCart();
    quantity = parseInt(quantity);
    
    if (quantity <= 0) {
        delete cart[productId];
        showNotification('Produkt byl odebrán z košíku', 'warning');
    } else {
        cart[productId] = quantity;
        showNotification('Množství bylo upraveno');
    }
    
    saveCart(cart);
    if (window.loadCart) {
        loadCart();  // Reload cart page if we're on it
    }
}

function clearCart() {
    localStorage.removeItem('cart');
    updateCartCount();
    if (window.loadCart) {
        loadCart();
    }
    showNotification('Košík byl vyprázdněn', 'warning');
}

function updateCartCount() {
    const cart = getCart();
    const count = Object.values(cart).reduce((sum, quantity) => sum + quantity, 0);
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        cartCountElement.textContent = count;
        cartCountElement.classList.toggle('visible', count > 0);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {    const style = document.createElement('style');
    style.textContent = `
        #notification-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .notification {
            min-width: 300px;
            padding: 1rem;
            border-radius: 8px;
            animation: slideIn 0.3s ease;
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-left: 4px solid var(--color-forest);
        }
        
        .notification.warning {
            border-left-color: #dc3545;
        }
        
        .notification-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }
        
        .notification button {
            background: none;
            border: none;
            font-size: 1.25rem;
            cursor: pointer;
            color: #666;
            padding: 0;
        }
        
        .notification button:hover {
            color: #333;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Initialize cart count
    updateCartCount();

    // Add event listeners to "Add to Cart" buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', (e) => {
            const productId = e.target.closest('.add-to-cart').dataset.productId;
            if (productId) {
                addToCart(productId);
            }
        });
    });

    // Add event listeners to "Remove from Cart" buttons on cart page
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', (e) => {
            const productId = e.target.dataset.productId;
            if (productId) {
                removeFromCart(productId);
                const itemElement = e.target.closest('.cart-item');
                if (itemElement) {
                    itemElement.remove();
                }
                updateCartDisplay();
            }
        });
    });

    // Clear cart button
    const clearCartButton = document.getElementById('clear-cart');    if (clearCartButton) {
        clearCartButton.addEventListener('click', () => {
            if (confirm('Opravdu chcete vysypat košík?')) {
                clearCart();
            }
        });
    }

    updateCartDisplay();
});

async function updateCartDisplay() {
    const cartItemsContainer = document.getElementById('cart-items');
    if (!cartItemsContainer) return;

    const cart = getCart();
    const items = Object.entries(cart);

    if (items.length === 0) {
        cartItemsContainer.innerHTML = '<div class="cart-message">Váš košík je prázdný</div>';
        return;
    }

    try {
        const response = await fetch('/api/products/details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                slugs: items.map(([slug]) => slug)
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch product details');
        }
        
        const products = await response.json();
        if ('error' in products) {
            throw new Error(products.error);
        }
        
        let total = 0;
        cartItemsContainer.innerHTML = items.map(([slug, quantity]) => {
            const product = products[slug];
            if (!product) return '';
            
            const itemTotal = product.price * quantity;
            total += itemTotal;
            
            return `
                <div class="cart-item" data-product-slug="${slug}">
                    <div class="cart-item-image">
                        <img src="${product.image.startsWith('http') ? product.image : '/uploads/' + product.image}" 
                             alt="${product.name}">
                    </div>
                    <div class="cart-item-info">
                        <h3>${product.name}</h3>
                        <div class="cart-item-price">${product.price.toFixed(2)} Kč</div>
                        <div class="cart-item-controls">
                            <div class="quantity-control">
                                <button class="quantity-btn" onclick="updateQuantity('${slug}', ${quantity - 1})">-</button>
                                <span>${quantity}</span>
                                <button class="quantity-btn" onclick="updateQuantity('${slug}', ${quantity + 1})">+</button>
                            </div>
                            <button class="remove-btn" onclick="removeFromCart('${slug}')">
                                <i class="fas fa-trash"></i> Odstranit
                            </button>
                        </div>
                    </div>
                    <div class="cart-item-total">
                        ${itemTotal.toFixed(2)} Kč
                    </div>
                </div>
            `;
        }).join('');
        
        document.getElementById('cart-subtotal').textContent = `${total.toFixed(2)} Kč`;
        document.getElementById('cart-total').textContent = `${total.toFixed(2)} Kč`;
    } catch (error) {
        console.error('Error loading cart:', error);
        cartItemsContainer.innerHTML = '<div class="cart-message">Chyba při načítání košíku</div>';
        showNotification('Chyba při načítání košíku', 'warning');
    }
}