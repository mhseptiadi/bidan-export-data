
$(function(){
	$('#button-get').attr("disabled", false);

    $('form#signin').submit(function(){
		$(this).find('button[type=submit]').attr('disabled', 'disabled');
		$('#spinner').show();
	});

	$('form#down_all').submit(function(){
		$(this).find('button[type=submit]').attr('disabled', 'disabled');
		$('#spinner').show();
	});

	$('#select_all').change(function() {
	    var checkboxes = $(this).closest('form').find(':checkbox');
	    if($(this).is(':checked')) {
	        checkboxes.prop('checked', true);
	    } else {
	        checkboxes.prop('checked', false);
	    }
	});

});