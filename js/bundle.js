class BundleEngine {
    static discountAmount = 0;
    static BUNDLE_PRICE = 50.00;

    static calculateTotal(cart) {
        let totalDiscount = 0;

        // Group cart by nation
        const nationCounts = {};

        cart.forEach(item => {
            const nation = item.product.nation;
            if (!nationCounts[nation]) {
                nationCounts[nation] = { shirt: 0, balaclava: 0, flag: 0 };
            }
            if (item.product.type === productTypes.SHIRT) nationCounts[nation].shirt += item.qty;
            if (item.product.type === productTypes.BALACLAVA) nationCounts[nation].balaclava += item.qty;
            if (item.product.type === productTypes.FLAG) nationCounts[nation].flag += item.qty;
        });

        // Calculate bundles
        nations.forEach(nation => {
            const counts = nationCounts[nation.id];
            if (counts) {
                const bundles = Math.min(counts.shirt, counts.balaclava, counts.flag);
                if (bundles > 0) {
                    // Regular price for 1 set
                    const shirtPrice = products.find(p => p.nation === nation.id && p.type === productTypes.SHIRT)?.price || 0;
                    const balaclavaPrice = products.find(p => p.nation === nation.id && p.type === productTypes.BALACLAVA)?.price || 0;
                    const flagPrice = products.find(p => p.nation === nation.id && p.type === productTypes.FLAG)?.price || 0;

                    const setPrice = shirtPrice + balaclavaPrice + flagPrice;
                    const discountPerBundle = setPrice - this.BUNDLE_PRICE;

                    if (discountPerBundle > 0) {
                        totalDiscount += discountPerBundle * bundles;
                    }
                }
            }
        });

        this.discountAmount = totalDiscount;
        if (typeof window.updateCartUI === 'function') {
            window.updateCartUI(); // re-render to show discount
        }
    }

    static getDiscount() {
        return this.discountAmount;
    }

    static renderBundleUI(product) {
        // Find the bundle section placeholder in modal
        let bundleSection = document.querySelector('.js-bundle-ui');

        if (!bundleSection) {
            // It might not exist yet, we inject it below the Add to cart button or price
            const parent = document.querySelector('.p-t-33');
            if (parent) {
                const div = document.createElement('div');
                div.className = 'js-bundle-ui p-t-20 p-b-20 bor-top-1 m-t-20';
                parent.appendChild(div);
                bundleSection = div;
            } else {
                return;
            }
        }

        // Only show bundle UI if the product is a SHIRT
        if (product.type !== productTypes.SHIRT) {
            bundleSection.innerHTML = '';
            bundleSection.style.display = 'none';
            return;
        }

        const nation = product.nation;
        const matchingBalaclava = products.find(p => p.nation === nation && p.type === productTypes.BALACLAVA);
        const matchingFlag = products.find(p => p.nation === nation && p.type === productTypes.FLAG);

        if (!matchingBalaclava || !matchingFlag) {
            const balaclava = products.find(p => p.nation === nation && p.type === productTypes.BALACLAVA);
            const flag = products.find(p => p.nation === nation && p.type === productTypes.FLAG);

            const hasBalaclava = !!balaclava;
            const hasFlag = !!flag;

            if (!hasBalaclava && !hasFlag) { // If neither balaclava nor flag is available, hide the bundle section
                bundleSection.innerHTML = '';
                bundleSection.style.display = 'none';
                return;
            }

            bundleSection.style.display = 'block';
            const container = document.createElement('div');
            // Improved Styling: Solid red border to highlight bundle
            container.className = 'matchday-bundle-builder bg-light p-all-20 bor10 m-t-20 m-b-20';
            container.style.border = '2px dashed #fa4251';
            container.innerHTML = `
            <h5 class="mtext-105 cl2 p-b-10" style="color: #fa4251;">
                <i class="zmdi zmdi-fire m-r-5"></i> Stell dir dein Matchday-Paket zusammen & spare!
            </h5>
            <p class="stext-102 cl3 p-b-15">
                Kombiniere dieses Trikot mit der passenden <strong>Sturmmaske</strong> und <strong>Nationalfahne</strong> für nur <strong>€${this.BUNDLE_PRICE.toFixed(2)}</strong>.
            </p>
            <div class="bundle-options m-b-15">
                <div class="flex-w flex-m m-b-10">
                    <input class="m-r-10" type="checkbox" id="bundle-balaclava" ${hasBalaclava ? 'checked' : ''} ${hasBalaclava ? '' : 'disabled'}>
                    <label for="bundle-balaclava" class="stext-102 cl3 m-b-0">
                        ${balaclava ? `Dazu: ${balaclava.name} (+€${balaclava.price.toFixed(2)})` : 'Sturmmaske nicht verfügbar'}
                    </label>
                </div>
                <div class="flex-w flex-m m-b-10">
                    <input class="m-r-10" type="checkbox" id="bundle-flag" ${hasFlag ? 'checked' : ''} ${hasFlag ? '' : 'disabled'}>
                    <label for="bundle-flag" class="stext-102 cl3 m-b-0">
                        ${flag ? `Dazu: ${flag.name} (+€${flag.price.toFixed(2)})` : 'Fahne nicht verfügbar'}
                    </label>
                </div>
            </div>
            <button id="btn-add-bundle" class="flex-c-m stext-101 cl0 size-101 bg1 bor1 hov-btn1 p-lr-15 trans-04 w-full">
                Paket in den Warenkorb (€${this.BUNDLE_PRICE.toFixed(2)})
            </button>
        `;
            bundleSection.innerHTML = ''; // Clear existing content
            bundleSection.appendChild(container);

            // Add event listener to the new bundle button
            const btnBox = bundleSection.querySelector('#btn-add-bundle');
            const cbBalaclava = bundleSection.querySelector('#bundle-balaclava');
            const cbFlag = bundleSection.querySelector('#bundle-flag');

            // Dynamic price update when checkboxes change
            const updatePriceDisplay = () => {
                const addBalaclava = cbBalaclava && cbBalaclava.checked && !cbBalaclava.disabled;
                const addFlag = cbFlag && cbFlag.checked && !cbFlag.disabled;

                if (addBalaclava && addFlag) {
                    btnBox.textContent = `Paket in den Warenkorb (€${this.BUNDLE_PRICE.toFixed(2)})`;
                    // Green color for bundle confirmation
                    btnBox.classList.remove('bg1');
                    btnBox.style.backgroundColor = '#00ad5f';
                    btnBox.style.borderColor = '#00ad5f';
                } else {
                    let total = product.price;
                    if (addBalaclava && balaclava) total += balaclava.price;
                    if (addFlag && flag) total += flag.price;
                    btnBox.textContent = `In den Warenkorb (€${total.toFixed(2)})`;

                    // Reset to standard block color
                    btnBox.style.backgroundColor = '';
                    btnBox.style.borderColor = '';
                    btnBox.classList.add('bg1');
                }
            };

            if (cbBalaclava) cbBalaclava.addEventListener('change', updatePriceDisplay);
            if (cbFlag) cbFlag.addEventListener('change', updatePriceDisplay);
            updatePriceDisplay(); // Initial display

            btnBox.addEventListener('click', (e) => {
                e.preventDefault();
                const names = [product.name];

                const addBalaclava = cbBalaclava && cbBalaclava.checked && !cbBalaclava.disabled;
                const addFlag = cbFlag && cbFlag.checked && !cbFlag.disabled;

                // Add shirt
                window.addToCart(product, 1); // Always add 1 shirt for bundle

                // Add other items if checked
                if (addBalaclava) {
                    window.addToCart(balaclava, 1);
                    names.push(balaclava.name);
                }
                if (addFlag) {
                    window.addToCart(flag, 1);
                    names.push(flag.name);
                }

                // Using standard template swal
                swal(names.join(", "), "wurde in den Warenkorb gelegt!", "success");

                // Close modal (if inside quick view)
                const hideModalBtn = document.querySelector('.js-hide-modal1');
                if (hideModalBtn) {
                    hideModalBtn.click();
                }
            });
        }
    }
}

window.BundleEngine = BundleEngine;
