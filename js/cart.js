// Load cart from localStorage on startup
let cart = JSON.parse(localStorage.getItem('wcs_cart') || '[]');

function saveCart() {
    localStorage.setItem('wcs_cart', JSON.stringify(cart));
}

function addToCart(product, qty = 1) {
    const existing = cart.find(item => item.product.id === product.id);
    if (existing) {
        existing.qty += qty;
    } else {
        cart.push({ product, qty });
    }
    saveCart();
    updateCartUI();

    if (typeof window.BundleEngine !== 'undefined') {
        window.BundleEngine.calculateTotal(cart);
    }
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.product.id !== productId);
    saveCart();
    updateCartUI();

    if (typeof window.BundleEngine !== 'undefined') {
        window.BundleEngine.calculateTotal(cart);
    }
}

function getCart() {
    return cart;
}

function updateCartUI() {
    let totalItems = 0;
    let totalPrice = 0;

    const wrapItems = document.querySelector('.header-cart-wrapitem');
    if (wrapItems) {
        wrapItems.innerHTML = '';
        cart.forEach(item => {
            totalItems += item.qty;
            if (!item || !item.product) {
                console.error("Invalid cart item:", item);
                return;
            }
            const price = item.product.price || 0;
            const itemTotal = (item.product.discountedPrice !== undefined) ? item.product.discountedPrice : price;
            totalPrice += itemTotal * item.qty;

            const li = document.createElement('li');
            li.className = 'header-cart-item flex-w flex-t m-b-12';
            li.innerHTML = `
                <div class="header-cart-item-img" onclick="removeFromCart('${item.product.id}')">
                    <img src="${item.product.image || ''}" alt="${item.product.name || 'Produkt'}" loading="lazy">
                </div>

                <div class="header-cart-item-txt p-t-8">
                    <a href="#" class="header-cart-item-name m-b-18 hov-cl1 trans-04">
                        ${item.product.name || 'Unknown'}
                    </a>

                    <span class="header-cart-item-info">
                        ${item.qty} x €${itemTotal.toFixed(2)}
                    </span>
                </div>
            `;
            wrapItems.appendChild(li);
        });
    }

    let displayTotal = totalPrice;
    if (window.BundleEngine && window.BundleEngine.getDiscount() > 0) {
        const discount = window.BundleEngine.getDiscount();
        displayTotal -= discount;

        const li = document.createElement('li');
        li.className = 'header-cart-item flex-w flex-t m-b-12';
        li.innerHTML = `
            <div class="header-cart-item-txt p-t-8 w-full p-l-0">
                <span class="header-cart-item-name m-b-18 hov-cl1 trans-04" style="color:#fa4251;">
                    Matchday-Paket Ersparnis
                </span>
                <span class="header-cart-item-info text-right w-full" style="color:#fa4251;">
                    - €${discount.toFixed(2)}
                </span>
            </div>
        `;
        wrapItems.appendChild(li);
    }

    const totalEl = document.querySelector('.header-cart-total');
    if (totalEl) {
        totalEl.innerHTML = `Gesamt: €${displayTotal.toFixed(2)}`;
    }

    const badges = document.querySelectorAll('.js-show-cart');
    badges.forEach(badge => {
        badge.setAttribute('data-notify', totalItems.toString());
    });

    // Update cart count in header
    const countEls = document.querySelectorAll('.js-cart-header-count');
    countEls.forEach(el => { el.textContent = totalItems; });
}

// Ensure global scope
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.getCart = getCart;
window.updateCartUI = updateCartUI;

document.addEventListener('DOMContentLoaded', () => {
    updateCartUI();
});
