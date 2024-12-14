document.addEventListener('DOMContentLoaded', function() {
    // Select All functionality
    const selectAllCheckbox = document.getElementById('selectAll');
    const memberCheckboxes = document.querySelectorAll('.member-checkbox');
    
    // Sorting functionality
    const sortDropdown = document.querySelector('.dropdown-menu');
    const memberGrid = document.querySelector('.member-grid');
    
    sortDropdown.addEventListener('click', function(e) {
        if (e.target.classList.contains('dropdown-item')) {
            e.preventDefault();
            const sortType = e.target.dataset.sort;
            const members = Array.from(document.querySelectorAll('.member-card'));
            
            members.sort((a, b) => {
                const nameA = a.querySelector('h3').textContent.trim();
                const nameB = b.querySelector('h3').textContent.trim();
                
                if (sortType === 'last-name-asc') {
                    return nameA.localeCompare(nameB);
                } else if (sortType === 'last-name-desc') {
                    return nameB.localeCompare(nameA);
                } else if (sortType === 'first-name-asc') {
                    return nameA.split(', ')[1].localeCompare(nameB.split(', ')[1]);
                } else if (sortType === 'first-name-desc') {
                    return nameB.split(', ')[1].localeCompare(nameA.split(', ')[1]);
                }
            });
            
            members.forEach(member => memberGrid.appendChild(member));
        }
    });

    selectAllCheckbox.addEventListener('change', function() {
        memberCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateActionButtons();
    });

    // Individual checkbox handling
    memberCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateActionButtons();
            // Update select all checkbox
            selectAllCheckbox.checked = 
                Array.from(memberCheckboxes).every(cb => cb.checked);
        });
    });

    // Search functionality
    const searchInput = document.querySelector('.search-box input');
    const memberCards = document.querySelectorAll('.member-card');

    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        
        memberCards.forEach(card => {
            const memberInfo = card.querySelector('.member-info').textContent.toLowerCase();
            card.style.display = memberInfo.includes(searchTerm) ? '' : 'none';
        });
    });

    // Update action buttons based on selection
    function updateActionButtons() {
        const selectedCount = document.querySelectorAll('.member-checkbox:checked').length;
        const actionButtons = document.querySelectorAll('.action-buttons .btn');
        
        actionButtons.forEach(button => {
            button.disabled = selectedCount === 0;
        });
    }

    // Initialize action buttons state
    updateActionButtons();
});
