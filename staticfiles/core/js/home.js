function openProductModal(product) {
    document.getElementById("modalImage").src = product.image;
    document.getElementById("modalTitle").innerText = product.title;
    document.getElementById("modalPrice").innerText = product.price;
    document.getElementById("modalDescription").innerText = product.description;
    document.getElementById("modalSite").innerText = "Mağaza: " + product.site;
    document.getElementById("modalLink").href = product.link;
    const thumbs = document.getElementById("modalThumbs");
    if (thumbs) {
        thumbs.innerHTML = "";
        const images = Array.isArray(product.images) ? product.images : [];
        images.forEach((src) => {
            if (!src) return;
            const img = document.createElement("img");
            img.src = src;
            img.alt = product.title || "Ürün";
            img.addEventListener("click", () => {
                document.getElementById("modalImage").src = src;
            });
            thumbs.appendChild(img);
        });
    }
    document.getElementById("productModal").style.display = "flex";
}

function closeProductModal() {
    document.getElementById("productModal").style.display = "none";
}

function addToCart() {
    const title = document.getElementById('modalTitle').innerText;
    alert(title + ' sepete eklendi.');
    closeProductModal();
}

function openProductModalFromElement(element) {
    const product = {
        title: element.dataset.productTitle,
        price: element.dataset.productPrice,
        image: element.dataset.productImage,
        images: element.dataset.productImages ? element.dataset.productImages.split("|") : [],
        description: element.dataset.productDescription,
        site: element.dataset.productSite,
        link: element.dataset.productLink
    };
    openProductModal(product);
}

function searchProductBySameBrand(productTitle, site) {
    const encodedTitle = encodeURIComponent(productTitle);
    window.location.href = `/?query=${encodedTitle}&compare=true`;
}

function showAISummaryAfterImages() {
    const images = document.querySelectorAll('.product-image img, .compare-large .product-image img, .thumb-card img');
    if (images.length === 0) {
        const summaries = document.querySelectorAll('.ai-summary');
        summaries.forEach(summary => summary.classList.add('visible'));
        return;
    }

    let loadedCount = 0;
    const totalImages = images.length;
    let showTimeout;

    function showSummaries() {
        const summaries = document.querySelectorAll('.ai-summary');
        summaries.forEach(summary => summary.classList.add('visible'));
    }

    images.forEach(img => {
        if (img.complete) {
            loadedCount++;
        } else {
            img.addEventListener('load', () => {
                loadedCount++;
                if (loadedCount === totalImages) {
                    clearTimeout(showTimeout);
                    showSummaries();
                }
            });
            img.addEventListener('error', () => {
                loadedCount++;
                if (loadedCount === totalImages) {
                    clearTimeout(showTimeout);
                    showSummaries();
                }
            });
        }
    });

    if (loadedCount === totalImages) {
        showSummaries();
    } else {
        showTimeout = setTimeout(showSummaries, 2000);
    }
}

function colorizeAirlines(root = document) {
    const badges = root.querySelectorAll('.airline-badge[data-airline]');
    const brand = {
        "TK": { bg: "#fee2e2", border: "#fecaca", text: "#991b1b" }, // Turkish Airlines
        "PC": { bg: "#ede9fe", border: "#ddd6fe", text: "#5b21b6" }, // Pegasus
        "XQ": { bg: "#fff7ed", border: "#fed7aa", text: "#9a3412" }, // SunExpress
        "VF": { bg: "#ecfeff", border: "#a5f3fc", text: "#0e7490" }, // AJet
        "AJ": { bg: "#f0f9ff", border: "#bae6fd", text: "#0369a1" }  // Anadolujet (legacy)
    };
    badges.forEach(badge => {
        const code = (badge.dataset.airline || 'XX').toUpperCase();
        if (brand[code]) {
            badge.style.setProperty('--badge-bg', brand[code].bg);
            badge.style.setProperty('--badge-border', brand[code].border);
            badge.style.setProperty('--badge-text', brand[code].text);
            return;
        }
        let hash = 0;
        for (let i = 0; i < code.length; i++) {
            hash = ((hash << 5) - hash) + code.charCodeAt(i);
            hash |= 0;
        }
        const hue = Math.abs(hash) % 360;
        badge.style.setProperty('--badge-bg', `hsl(${hue} 70% 92%)`);
        badge.style.setProperty('--badge-border', `hsl(${hue} 70% 80%)`);
        badge.style.setProperty('--badge-text', `hsl(${hue} 55% 28%)`);
    });
}

function swapMainProduct(elem) {
    const dataset = elem.dataset;
    const mainImage = document.querySelector('.compare-large .product-image img');
    const mainTitle = document.querySelector('.compare-large .product-title');
    const mainPrice = document.querySelector('.compare-large .product-price');
    const mainDesc = document.querySelector('.compare-large .product-body > p');
    const mainSiteBadge = document.querySelector('.compare-large .product-header .site-badge');
    const mainLink = document.querySelector('.compare-large .btn-primary');

    if (mainImage && dataset.productImage) mainImage.src = dataset.productImage;
    if (mainTitle && dataset.productTitle) mainTitle.innerText = dataset.productTitle;
    if (mainPrice && dataset.productPrice) mainPrice.innerText = dataset.productPrice;
    if (mainDesc && dataset.productDescription) mainDesc.innerText = dataset.productDescription;
    if (mainSiteBadge && dataset.productSite) mainSiteBadge.innerText = dataset.productSite;
    if (mainLink && dataset.productLink) mainLink.href = dataset.productLink;

    const thumbStrip = document.querySelector('.compare-large .thumb-strip');
    if (thumbStrip) {
        thumbStrip.innerHTML = "";
        const images = dataset.productImages ? dataset.productImages.split("|") : [];
        if (images.length === 0 && dataset.productImage) {
            images.push(dataset.productImage);
        }
        images.forEach((src) => {
            if (!src) return;
            const img = document.createElement("img");
            img.src = src;
            img.alt = dataset.productTitle || "Ürün";
            img.dataset.image = src;
            thumbStrip.appendChild(img);
        });
        const first = thumbStrip.querySelector('img');
        if (first) first.classList.add('active');
        bindCompareThumbs();
    }
}

function bindCompareThumbs() {
    const thumbs = document.querySelectorAll('.thumb-strip img');
    thumbs.forEach(thumb => {
        const handler = (event) => {
            event.stopPropagation();
            const img = event.currentTarget;
            const src = img.dataset.image || img.getAttribute('src');
            const mainImage = img.closest('.compare-large')?.querySelector('.product-image img');
            if (mainImage && src) {
                mainImage.classList.add('is-swapping');
                mainImage.src = src;
                setTimeout(() => mainImage.classList.remove('is-swapping'), 200);
            }
            const allThumbs = img.closest('.thumb-strip')?.querySelectorAll('img') || [];
            allThumbs.forEach(t => t.classList.remove('active'));
            img.classList.add('active');
        };
        thumb.addEventListener('click', handler);
        thumb.addEventListener('mouseenter', handler);
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const targets = document.querySelectorAll(".typing-target");
    targets.forEach(target => {
        const text = target.dataset.text;
        let i = 0;
        target.innerHTML = "";
        function type() {
            if (i < text.length) {
                target.innerHTML += text.charAt(i);
                i++;
                setTimeout(type, 20);
            }
        }
        type();
    });

    showAISummaryAfterImages();
    bindCompareThumbs();
    colorizeAirlines();

    document.addEventListener('click', (event) => {
        const target = event.target.closest('[data-loading="true"]');
        if (target && typeof window.setLoading === 'function') {
            window.setLoading(true);
        }
    });

    setTimeout(() => {
        const compareSections = document.querySelectorAll('[id^="compare-section-"]');
        if (compareSections.length > 0) {
            const lastCompare = compareSections[compareSections.length - 1];
            lastCompare.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 300);
});
