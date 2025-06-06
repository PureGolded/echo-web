class ProductFilter {
    constructor(options) {
        this.options = {
            productSelector: '.product-card',
            brandSelector: 'data-brand',
            tagSelector: 'data-tags',
            ...options
        };
        
        this.products = document.querySelectorAll(this.options.productSelector);
        this.init();
    }
    
    init() {
        // Set up event listeners
        if (this.options.brandFilterId) {
            const brandFilter = document.getElementById(this.options.brandFilterId);
            if (brandFilter) {
                brandFilter.addEventListener('change', () => this.filterProducts());
            }
        }
        
        if (this.options.tagFilterId) {
            const tagFilter = document.getElementById(this.options.tagFilterId);
            if (tagFilter) {
                tagFilter.addEventListener('change', () => this.filterProducts());
            }
        }
        
        if (this.options.sortSelectId) {
            const sortSelect = document.getElementById(this.options.sortSelectId);
            if (sortSelect) {
                sortSelect.addEventListener('change', () => this.sortProducts());
            }
        }
    }
    
    filterProducts() {
        let selectedBrand = '';
        let selectedTag = '';
        
        // Get selected brand if the filter exists
        if (this.options.brandFilterId) {
            const brandFilter = document.getElementById(this.options.brandFilterId);
            if (brandFilter) {
                selectedBrand = brandFilter.value;
            }
        }
        
        // Get selected tag if the filter exists
        if (this.options.tagFilterId) {
            const tagFilter = document.getElementById(this.options.tagFilterId);
            if (tagFilter) {
                selectedTag = tagFilter.value;
            }
        }
        
        // Filter products based on selections
        this.products.forEach(product => {
            const productBrand = product.getAttribute(this.options.brandSelector);
            const productTags = product.getAttribute(this.options.tagSelector) || '';
            const tagArray = productTags.split(',').map(tag => tag.trim());
            
            let showProduct = true;
            
            // Apply brand filter if selected
            if (selectedBrand && selectedBrand !== 'all') {
                showProduct = showProduct && (productBrand === selectedBrand);
            }
            
            // Apply tag filter if selected
            if (selectedTag && selectedTag !== 'all') {
                showProduct = showProduct && tagArray.includes(selectedTag);
            }
            
            // Show or hide product
            product.style.display = showProduct ? '' : 'none';
        });
    }
    
    sortProducts() {
        if (!this.options.sortSelectId) return;
        
        const sortSelect = document.getElementById(this.options.sortSelectId);
        if (!sortSelect) return;
        
        const sortValue = sortSelect.value;
        const productGrid = this.products[0]?.parentNode;
        if (!productGrid) return;
        
        // Convert NodeList to Array for sorting
        const productsArray = Array.from(this.products);
        
        // Sort products
        if (sortValue === 'name-asc') {
            productsArray.sort((a, b) => {
                const nameA = a.querySelector('h3')?.textContent.toLowerCase() || '';
                const nameB = b.querySelector('h3')?.textContent.toLowerCase() || '';
                return nameA.localeCompare(nameB);
            });
        } else if (sortValue === 'name-desc') {
            productsArray.sort((a, b) => {
                const nameA = a.querySelector('h3')?.textContent.toLowerCase() || '';
                const nameB = b.querySelector('h3')?.textContent.toLowerCase() || '';
                return nameB.localeCompare(nameA);
            });
        } else if (sortValue === 'price-asc') {
            productsArray.sort((a, b) => {
                const priceA = this.extractPrice(a) || 0;
                const priceB = this.extractPrice(b) || 0;
                return priceA - priceB;
            });
        } else if (sortValue === 'price-desc') {
            productsArray.sort((a, b) => {
                const priceA = this.extractPrice(a) || 0;
                const priceB = this.extractPrice(b) || 0;
                return priceB - priceA;
            });
        }
        
        // Re-append sorted products
        productsArray.forEach(product => {
            productGrid.appendChild(product);
        });
    }
    
    extractPrice(productEl) {
        const priceEl = productEl.querySelector('.tag.price');
        if (!priceEl) return 0;
        
        const priceText = priceEl.textContent || '';
        const priceMatch = priceText.match(/\d+(\.\d+)?/);
        return priceMatch ? parseFloat(priceMatch[0]) : 0;
    }
}