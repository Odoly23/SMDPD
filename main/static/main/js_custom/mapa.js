/* Mapa Timor-Leste (Highcharts Maps): total membru tuir munisipiu. Data husi API [[xave, total], ...]. */
document.addEventListener('DOMContentLoaded', function () {
	var el = document.getElementById('map-container');
	if (!el) { return; }
	fetch(el.getAttribute('data-url'), { credentials: 'same-origin' })
		.then(function (response) { return response.json(); })
		.then(function (dataFromAPI) {
			Highcharts.mapChart('map-container', {
				chart: { map: 'countries/tl/tl-all' },
				title: { text: 'Mapa Dadus Membru Tuir Munisipiu iha Timor-Leste' },
				subtitle: { text: '' },
				lang: { noData: 'Laiha data' },
				mapNavigation: { enabled: true, buttonOptions: { verticalAlign: 'bottom' } },
				colorAxis: { min: 0, minColor: '#e6f6ee', maxColor: '#00a853' },
				series: [{
					name: 'Munisipiu',
					nullColor: '#E0E0E0',
					borderColor: '#606060',
					data: dataFromAPI,
					states: { hover: { color: '#02b0ed' } },
					dataLabels: { enabled: true, format: '{point.name}' },
					tooltip: { pointFormat: '{point.name}: <b>{point.value}</b> membru' }
				}]
			});
		});
});
