/* DataTables standar SMDPD ba tabela ki'ik (la iha server-side). */
$(document).ready(function () {
	var $t = $('table.datatable');
	if (!$t.length) { return; }
	$t.each(function () {
		var $x = $(this);
		$x.removeAttr('width').DataTable({
			pageLength: 25,
			order: [],
			language: {
				search: 'Buka:', lengthMenu: 'Hatudu _MENU_', info: 'Hatudu _START_ to _END_ husi _TOTAL_',
				infoEmpty: 'Laiha data', zeroRecords: 'Laiha data ne\'ebé hanesan',
				paginate: { previous: 'Antes', next: 'Tuir' }
			}
		});
	});
});
