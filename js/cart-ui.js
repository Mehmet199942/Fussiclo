const updateUI = () => {
    const cart = getCart();
    let totalItems = 0;
    let totalPrice = 0;

    // 1. Update Header Badge
    const badges = document.querySelectorAll('.js-show-cart, .icon-header-noti');
    const headerCountText = document.querySelectorAll('.js-cart-header-count');
    cart.forEach(item => {
        if (item && item.qty) totalItems += item.qty;
    });
    badges.forEach(badge => badge.setAttribute('data-notify', totalItems));
    headerCountText.forEach(span => span.innerText = totalItems);
    
    // 2. Update Header Cart Drawer
    const wrapItems = document.querySelector('.header-cart-wrapitem');
    if (wrapItems) {
        wrapItems.innerHTML = '';
        cart.forEach(item => {
            if (!item || !item.product) return; // Skip corrupted items
            const p = item.product;
            const price = parseFloat(p.discountedPrice || p.price) || 0;
            totalPrice += price * (item.qty || 1);

            const li = document.createElement('li');
            li.className = 'header-cart-item flex-w flex-t m-b-12';
            li.innerHTML = `
                <div class="header-cart-item-img">
                    <img src="${p.image}" alt="IMG">
                </div>
                <div class="header-cart-item-txt p-t-8">
                    <a href="#" class="header-cart-item-name m-b-18 hov-cl1 trans-04">
                        ${p.name}
                    </a>
                    <span class="header-cart-item-info">
                        ${item.qty} x €${price.toFixed(2)}
                    </span>
                    <button class="remove-item-btn" data-id="${p.id}" style="color: #666; font-size: 11px; text-decoration: underline; margin-top: 5px; background: none; border: none; padding: 0;">Entfernen</button>
                </div>
            `;
            wrapItems.appendChild(li);
        });

        const totalEl = document.querySelector('.header-cart-total, .js-cart-total-price');
        if (totalEl) totalEl.innerText = `Gesamt: €${totalPrice.toFixed(2)}`;
    }
    
    // 3. Update Shopping Cart Page (if present)
    const cartPageItems = document.getElementById('cart-page-items');
    if (cartPageItems) {
        cartPageItems.innerHTML = cart.map(item => {
            if (!item || !item.product) return ''; // Skip corrupted items
            const p = item.product;
            const price = parseFloat(p.discountedPrice || p.price) || 0;
            const qty = item.qty || 1;
            return `
                <tr class="table_row">
                    <td class="column-1">
                        <div class="how-itemcart1">
                            <img src="${p.image}" alt="IMG">
                        </div>
                    </td>
                    <td class="column-2">${p.name}</td>
                    <td class="column-3">€${price.toFixed(2)}</td>
                    <td class="column-4">
                        <div class="wrap-num-product flex-w m-l-auto m-r-0">
                            <div class="btn-num-product-down cl8 hov-btn3 trans-04 flex-c-m" data-id="${p.id}">
                                <i class="fs-16 zmdi zmdi-minus"></i>
                            </div>
                            <input class="mtext-104 cl3 txt-center num-product" type="number" value="${qty}" readonly>
                            <div class="btn-num-product-up cl8 hov-btn3 trans-04 flex-c-m" data-id="${p.id}">
                                <i class="fs-16 zmdi zmdi-plus"></i>
                            </div>
                        </div>
                    </td>
                    <td class="column-5">€${(price * qty).toFixed(2)}</td>
                </tr>
            `;
        }).join('');
        
        const pageTotal = document.getElementById('cart-page-total');
        if (pageTotal) pageTotal.innerText = `€${totalPrice.toFixed(2)}`;
    }
};

// Initial Bindings
document.addEventListener('DOMContentLoaded', () => {
    updateUI();
    
    // Global Event Delegation for Dynamic Elements
    document.addEventListener('click', (e) => {

        // Remove item
        if (e.target.classList.contains('remove-item-btn')) {
            removeFromCart(e.target.dataset.id);
        }
        
        // Plus / Minus logic
        if (e.target.closest('.btn-num-product-up')) {
            const id = e.target.closest('.btn-num-product-up').dataset.id;
            const cart = getCart();
            const item = cart.find(i => i.product.id === id);
            if (item) updateQuantity(id, item.qty + 1);
        }
        
        if (e.target.closest('.btn-num-product-down')) {
            const id = e.target.closest('.btn-num-product-down').dataset.id;
            const cart = getCart();
            const item = cart.find(i => i.product.id === id);
            if (item) updateQuantity(id, item.qty - 1);
        }

        // --- Checkout Link / Button Interception ---
        const checkoutLink = e.target.closest('a[href="checkout.html"]') || e.target.closest('.js-btn-checkout');
        if (checkoutLink) {
            e.preventDefault();
            // Dynamically import checkout logic and trigger redirect
            import('./checkout.js').then(m => {
                m.initiateCheckout();
            }).catch(err => {
                console.error('Failed to load checkout script:', err);
                // Fallback to direct location change if import fails
                window.location.href = 'shoping-cart.html';
            });
        }
    });
    
    window.addEventListener('cartUpdated', updateUI);
});

// Expose functions globally for legacy scripts immediately upon module load
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.getCart = getCart;
window.updateQuantity = updateQuantity;
window.updateUI = updateUI;
