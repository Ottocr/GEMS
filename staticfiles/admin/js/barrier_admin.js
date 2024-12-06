(function($) {
    'use strict';
    $(document).ready(function() {
        // Function to update risk subtypes based on selected risk types
        function updateRiskSubtypes() {
            var selectedRiskTypes = $('#id_risk_types').val();
            var $subtypeSelect = $('#id_risk_subtypes');
            
            // Store currently selected subtypes
            var selectedSubtypes = $subtypeSelect.val() || [];
            
            // Clear and disable subtype select if no risk types selected
            if (!selectedRiskTypes || selectedRiskTypes.length === 0) {
                $subtypeSelect.empty().prop('disabled', true);
                return;
            }
            
            // Enable subtype select
            $subtypeSelect.prop('disabled', false);
            
            // Get subtypes for selected risk types
            $.ajax({
                url: '/admin/core/risksubtype/',
                data: {
                    'risk_type': selectedRiskTypes.join(',')
                },
                dataType: 'json',
                success: function(data) {
                    $subtypeSelect.empty();
                    
                    // Add options for each subtype
                    data.forEach(function(subtype) {
                        var option = new Option(
                            subtype.risk_type_name + ' - ' + subtype.name,
                            subtype.id,
                            false,
                            selectedSubtypes.includes(subtype.id.toString())
                        );
                        $subtypeSelect.append(option);
                    });
                    
                    // Trigger change event to update any dependent fields
                    $subtypeSelect.trigger('change');
                }
            });
        }
        
        // Update subtypes when risk types change
        $('#id_risk_types').on('change', updateRiskSubtypes);
        
        // Initial update on page load
        updateRiskSubtypes();
        
        // Handle effectiveness score fields
        function updateEffectivenessScores() {
            var $formRows = $('.barrier-effectiveness-score-form');
            
            $formRows.each(function() {
                var $row = $(this);
                var $riskTypeSelect = $row.find('.field-risk_type select');
                var $subtypeSelect = $row.find('.field-risk_subtype select');
                
                // Update subtypes when risk type changes
                $riskTypeSelect.on('change', function() {
                    var riskTypeId = $(this).val();
                    
                    if (!riskTypeId) {
                        $subtypeSelect.empty().prop('disabled', true);
                        return;
                    }
                    
                    $.ajax({
                        url: '/admin/core/risksubtype/',
                        data: { 'risk_type': riskTypeId },
                        dataType: 'json',
                        success: function(data) {
                            $subtypeSelect.empty().prop('disabled', false);
                            
                            // Add empty option
                            $subtypeSelect.append(new Option('---------', ''));
                            
                            // Add options for each subtype
                            data.forEach(function(subtype) {
                                $subtypeSelect.append(new Option(subtype.name, subtype.id));
                            });
                        }
                    });
                });
            });
        }
        
        // Initialize effectiveness score handling
        updateEffectivenessScores();
        
        // Handle dynamic form additions
        $(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName === 'effectiveness_scores') {
                updateEffectivenessScores();
            }
        });
    });
})(django.jQuery);
