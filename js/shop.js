document.addEventListener('DOMContentLoaded', function () {
    renderNationTabs();
    renderProducts();
    handleUrlFilter();
    initTimer();
    initSearch();
});

function renderNationTabs() {
    const filterGroup = document.querySelector('.filter-tope-group');
    const nationDropdown = document.querySelector('#nation-dropdown');
    const sidebarNations = document.querySelector('.js-sidebar-nations');
    const desktopNations = document.querySelector('.js-desktop-nations');
    const sidebarSearchInput = document.querySelector('#sidebar-nation-search-input');

    // Clear existing tabs
    if (filterGroup) {
        filterGroup.innerHTML = `
            <button class="stext-106 cl6 hov1 bor3 trans-04 m-r-32 m-tb-5 how-active1" data-filter="*" role="tab" aria-selected="true" tabindex="0">
                Alle Nationen
            </button>
        `;
    }

    const nationList = window.nations || nations;
    console.log("Rendering Nation Tabs. Nations found:", typeof nationList !== 'undefined' ? nationList.length : 'none');
    
    if (sidebarSearchInput) {
        sidebarSearchInput.addEventListener('input', function() {
            renderSidebarNations(this.value);
        });
    }

    renderSidebarNations('');

    if (!nationList) {
        console.error("Nations data is required but not found.");
        return;
    }

    nationList.forEach((nation, index) => {
        // ... (existing filterGroup and nationDropdown logic) ...
        if (filterGroup) {
            const btn = document.createElement('button');
            btn.className = 'stext-106 cl6 hov1 bor3 trans-04 m-r-32 m-tb-5';
            btn.setAttribute('data-filter', `.${nation.id}`);
            btn.setAttribute('data-nation-id', nation.id);
            btn.setAttribute('role', 'tab');
            btn.setAttribute('aria-selected', 'false');
            btn.setAttribute('tabindex', '0');
            btn.innerHTML = `${nation.name}`;

            btn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    btn.click();
                }
            });

            filterGroup.appendChild(btn);
        }

        if (nationDropdown) {
            const opt = document.createElement('option');
            opt.value = `.${nation.id}`;
            opt.textContent = nation.name;
            nationDropdown.appendChild(opt);
        }

        // Sidebar rendering is now handled by renderSidebarNations('') called above

        // Create Desktop Menu Link (Top 7 Pinned)
        if (desktopNations && index < 7) {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = `nation.html?nation=${nation.id}`;
            a.textContent = nation.name;
            li.appendChild(a);
            desktopNations.appendChild(li);
        }
    });

    if (filterGroup) {
        filterGroup.setAttribute('role', 'tablist');
    }

    // Attach Dropdown Sync behavior to Isotope filter
    if (nationDropdown) {
        // Destroy and re-init Select2 so it picks up the dynamic options
        if ($(nationDropdown).hasClass("select2-hidden-accessible")) {
            $(nationDropdown).select2('destroy');
        }
        $(nationDropdown).select2({
            minimumResultsForSearch: 20,
            dropdownParent: $(nationDropdown).next('.dropDownSelect2')
        });

        // We use jQuery because the template uses Select2 and Isotope via jQuery.
        $('#nation-dropdown').on('change', function () {
            const filterValue = $(this).val();

            // Sync the pill tabs UI (remove active class from all, add to matching)
            $('.filter-tope-group button').removeClass('how-active1');
            $(`.filter-tope-group button[data-filter="${filterValue}"]`).addClass('how-active1');

            // Trigger Combined Filter instead of direct filter to respect search
            if (typeof window.triggerCombinedFilter === 'function') {
                window.triggerCombinedFilter();
            } else {
                $('.isotope-grid').isotope({ filter: filterValue });
            }
        });

        // Also make sure clicking a tab updates the dropdown
        $('.filter-tope-group').on('click', 'button', function () {
            const filterValue = $(this).attr('data-filter');
            $('#nation-dropdown').val(filterValue).trigger('change.select2');
        });
    }
}

function renderSidebarNations(query) {
    const sidebarNations = document.querySelector('.js-sidebar-nations');
    if (!sidebarNations) return;

    const nationList = window.nations || (typeof nations !== 'undefined' ? nations : []);
    const q = (query || '').toLowerCase().trim();

    sidebarNations.innerHTML = '';

    // Always show special items if search is empty
    if (!q) {
        sidebarNations.innerHTML = `
            <a href="index.html" class="nation-field-item nation-field-special">
                <span class="nation-field-flag"><i class="zmdi zmdi-home"></i></span>
                <span class="nation-field-name">STARTSEITE</span>
            </a>
            <a href="product.html" class="nation-field-item nation-field-special">
                <span class="nation-field-flag"><i class="zmdi zmdi-apps"></i></span>
                <span class="nation-field-name">ALLE NATIONEN</span>
            </a>
        `;
    }

    nationList.forEach(nation => {
        if (q && !nation.name.toLowerCase().includes(q)) return;

        const flagHtml = nation.id === 'krd'
            ? '<span class="nation-field-flag">❤️☀️💚</span>'
            : `<span class="nation-field-flag"><img src="https://flagcdn.com/w80/${(nation.flagCode || nation.code).toLowerCase()}.png" alt="${nation.name}"></span>`;

        const a = document.createElement('a');
        a.href = `nation.html?nation=${nation.id}`;
        a.className = 'nation-field-item';
        a.innerHTML = `
            ${flagHtml}
            <span class="nation-field-name">${nation.name}</span>
        `;
        sidebarNations.appendChild(a);
    });
}

function renderProducts() {
    const grid = document.querySelector('.isotope-grid');
    if (!grid) return;

    grid.innerHTML = ''; // clear existing hardcoded

    products.forEach(product => {
        const html = `
            <div class="col-sm-6 col-md-4 col-lg-3 p-b-35 isotope-item ${product.nation}">
                <!-- Block2 -->
                <div class="block2">
                    <div class="block2-pic hov-img0">
                        <a href="${product.url || 'product-detail.html?id=' + product.id}">
                            <img src="${product.image}" alt="IMG-PRODUCT">
                        </a>

                        <a href="${product.url || 'product-detail.html?id=' + product.id}" class="block2-btn flex-c-m stext-103 cl2 size-102 bg0 bor2 hov-btn1 p-lr-15 trans-04">
                            Ansehen
                        </a>
                    </div>

                    <div class="block2-txt flex-w flex-t p-t-14">
                        <div class="block2-txt-child1 flex-col-l ">
                            <a href="${product.url || 'product-detail.html?id=' + product.id}" class="stext-104 cl4 hov-cl1 trans-04 js-name-b2 p-b-6">
                                ${product.name}
                            </a>

                            <span class="stext-105 cl3">
                                €${product.price.toFixed(2)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        grid.insertAdjacentHTML('beforeend', html);
    });
}



function handleUrlFilter() {
    const urlParams = new URLSearchParams(window.location.search);
    const nationId = urlParams.get('nation');
    if (nationId) {
        window.addEventListener('load', () => {
            const btn = document.querySelector(`.filter-tope-group button[data-nation-id="${nationId}"]`);
            if (btn) {
                btn.click();
            }
        });
    }
}

function initTimer() {
    // Set a countdown datestamp 2 days and 15 mins from load time
    const endTime = new Date(new Date().getTime() + (2 * 24 * 60 + 15) * 60000);

    function update() {
        const now = new Date();
        const diff = endTime - now;

        if (diff <= 0) return;

        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const mins = Math.floor((diff / 1000 / 60) % 60);
        const secs = Math.floor((diff / 1000) % 60);

        const dEl = document.querySelector('#promo-timer .days');
        const hEl = document.querySelector('#promo-timer .hours');
        const mEl = document.querySelector('#promo-timer .minutes');
        const sEl = document.querySelector('#promo-timer .seconds');

        if (dEl) dEl.innerText = days;
        if (hEl) hEl.innerText = hours < 10 ? '0' + hours : hours;
        if (mEl) mEl.innerText = mins < 10 ? '0' + mins : mins;
        if (sEl) sEl.innerText = secs < 10 ? '0' + secs : secs;
    }

    update();
    setInterval(update, 1000);
}

function initSearch() {
    const searchInput = document.querySelector('input[name="search-product"]');

    window.triggerCombinedFilter = () => {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const activeNationBtn = document.querySelector('.filter-tope-group button.how-active1');
        const activeNation = activeNationBtn ? activeNationBtn.getAttribute('data-filter') : '*';

        $('.isotope-grid').isotope({
            filter: function () {
                const name = $(this).find('.js-name-b2').text().toLowerCase();
                const matchesSearch = !searchTerm || name.includes(searchTerm);

                // Active nation filter check. Isotope uses classes like .de, .br etc 
                // Using .is(activeNation) checks if the element has that class
                const matchesNation = activeNation === '*' || $(this).is(activeNation);

                return matchesSearch && matchesNation;
            }
        });
    };

    if (searchInput) {
        searchInput.addEventListener('input', window.triggerCombinedFilter);
    }
}

function renderRelatedProducts(currentId) {
    const container = document.querySelector('.slick2');
    if (!container) return;

    const currentProduct = products.find(p => p.id === currentId);
    if (!currentProduct) return;

    const explicitIds = (currentProduct.related_products || '').split(',').map(id => id.trim()).filter(id => id);
    let relatedList = [];
    const seenIds = new Set([currentId]);

    // 1. Explicit
    explicitIds.forEach(rid => {
        const found = products.find(p => p.id === rid);
        if (found && !seenIds.has(found.id)) {
            relatedList.push(found);
            seenIds.add(found.id);
        }
    });

    // 2. Same Nation
    if (relatedList.length < 4) {
        const nationMates = products.filter(p => p.nation === currentProduct.nation && !seenIds.has(p.id));
        const needed = 4 - relatedList.length;
        const shuffled = nationMates.sort(() => 0.5 - Math.random());
        const batch = shuffled.slice(0, needed);
        relatedList = [...relatedList, ...batch];
        batch.forEach(p => seenIds.add(p.id));
    }

    // 3. Others
    if (relatedList.length < 4) {
        const others = products.filter(p => !seenIds.has(p.id));
        const needed = 4 - relatedList.length;
        const shuffled = others.sort(() => 0.5 - Math.random());
        const batch = shuffled.slice(0, needed);
        relatedList = [...relatedList, ...batch];
    }

    if (relatedList.length === 0) return;

    // Destroy slick if already initialized
    if ($(container).hasClass('slick-initialized')) {
        $(container).slick('unslick');
    }

    container.innerHTML = relatedList.map(p => {
        const url = p.url || `product-detail.html?id=${p.id}`;
        return `
            <div class="item-slick2 p-l-15 p-r-15 p-t-15 p-b-15">
                <div class="block2">
                    <div class="block2-pic hov-img0 p-b-15" style="border-radius:15px;overflow:hidden;background:#f8f8f8;">
                        <img src="${p.image}" alt="${p.name}">
                        <a href="${url}" class="block2-btn flex-c-m stext-103 cl2 size-102 bg0 bor2 hov-btn1 p-lr-15 trans-04">Ansehen</a>
                    </div>
                    <div class="block2-txt flex-w flex-t p-t-14">
                        <div class="block2-txt-child1 flex-col-l">
                            <a href="${url}" class="stext-104 cl4 hov-cl1 trans-04 js-name-b2 p-b-6" style="font-family:Poppins-Bold;font-size:16px;">
                                ${p.name}
                            </a>
                            <span class="stext-105 cl3" style="color:#e50914;font-family:Poppins-Bold;">
                                €${p.price.toFixed(2)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Re-init slick
    $(container).slick({
        slidesToShow: 4,
        slidesToScroll: 2,
        infinite: true,
        autoplay: false,
        arrows: true,
        dots: false,
        responsive: [
            { breakpoint: 1200, settings: { slidesToShow: 4, slidesToScroll: 2 } },
            { breakpoint: 992,  settings: { slidesToShow: 3, slidesToScroll: 2 } },
            { breakpoint: 768,  settings: { slidesToShow: 2, slidesToScroll: 2 } },
            { breakpoint: 576,  settings: { slidesToShow: 2, slidesToScroll: 2 } },
            { breakpoint: 400,  settings: { slidesToShow: 2, slidesToScroll: 2 } }
        ]
    });
}
