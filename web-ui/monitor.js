// Vue.use(VueWebsocket, "localhost:5000");

// io.on('connection', function(){
// 	console.log('Connected!')
// })

// io.on('error', function(data){
// 	console.log('Error :(', data)
// })

// io.onopen = function () {
// 	// connection is opened and ready to use
// 	console.log('Connection opened')
// };

// io.onerror = function (error) {
// 	// an error occurred when sending/receiving data
// 	console.log('websocket error', error)
// };
// var connection = io.connect('ws://0.0.0.0:5000');



// var socket = new eio.Socket('ws://localhost:5000/');
// socket.on('open', function(){
// 	console.log('WS Open')
// 	socket.on('message', function(data){});
// 	socket.on('close', function(){});
// });

// socket.on('error', function(data){
// 	console.log('error',data)
// });


var app = new Vue({
	el: '#app',
	data: {
	 	
		connected:false,
		index :0,
		spot_chart : null,
		spot_chart_data: [],
		demand_chart : null,
		demand_chart_data: [],
		participants:[],
		sample_market_state:null,
		generation_chart_data: {},
		// chart_background_color:'#E4DFDA'
	},

	computed:{
		chart_background_color(){
			var style = getComputedStyle(document.body);
			return style.getPropertyValue('--chart-bg-color');
		},
		chart_text_color(){
			var style = getComputedStyle(document.body);
			return style.getPropertyValue('--text-color');
		}
	},
	

	mounted(){
		var socket = io('http://localhost:5000');
		socket.on('dispatched', function(market_state){
			// console.log('market_stateed',data)
			
			// console.log('updateing chart')
			
			// app.spot_chart_data.push();
			app.spot_chart_data.push([app.index, market_state['price']]);
			app.demand_chart_data.push([app.index, market_state['demand']]);
			// Add to generation chart data
			for(var gen in market_state['dispatch']){
				// If the generator is not in the charting data, put it in. 
				if(!(gen in app.generation_chart_data)){
					console.log('adding gen to gen chart data', gen);
					app.generation_chart_data[gen] = []
				}
				app.generation_chart_data[gen].push([app.index, market_state['dispatch'][gen]] )
			}
			
			//If it's been a while, update the sample market_state to provide metadata.
			if(app.index % 300 == 0){
				console.log('updating sample market_state')
				app.sample_market_state = market_state;
			}
			// Update the time index
			app.index = app.index+1;
			
		});
		socket.on('connect', function(){
			app.connected = true;
			console.log('connected')
		});
		socket.on('nem_joined', function(data){console.log('nem_joined',data)});
		socket.on('disconnect', function(){
			app.connected = false;
			console.log('disconnected')
		});
		
		this.spot_chart = Highcharts.chart('spot-chart-container', {
				chart: {
						zoomType: 'x',
						backgroundColor:this.chart_background_color,
				},
				title: {
						text: 'Spot Price',
						style: {
							color: this.chart_text_color
						}
				},
				subtitle: {
						text: document.ontouchstart === undefined ?
										'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
				},
				xAxis: {
						type: 'int'
				},
				yAxis: {
						title: {
								text: 'Spot Price $/MWh'
						}
				},
				legend: {
						enabled: false
				},
				plotOptions: {
						area: {
								fillColor: {
										linearGradient: {
												x1: 0,
												y1: 0,
												x2: 0,
												y2: 1
										},
										stops: [
												[0, Highcharts.getOptions().colors[0]],
												[1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
										]
								},
								marker: {
										radius: 2
								},
								lineWidth: 1,
								states: {
										hover: {
												lineWidth: 1
										}
								},
								threshold: null
						}
				},

				series: [{
						type: 'area',
						name: 'Spot Price $/MWh',
						data: this.spot_chart_data
				}]
		});

		this.demand_chart = Highcharts.chart('demand-chart-container', {
			
			chart: {
					zoomType: 'x',
					backgroundColor:this.chart_background_color,
			},
			title: {
					text: 'Demand',
					style: {
						color: this.chart_text_color
					}
			},
			subtitle: {
					text: document.ontouchstart === undefined ?
									'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
			},
			xAxis: {
					type: 'int'
			},
			yAxis: {
					title: {
							text: 'Demand MWh'
					}
			},
			legend: {
					enabled: false
			},
			plotOptions: {
					area: {
							fillColor: {
									linearGradient: {
											x1: 0,
											y1: 0,
											x2: 0,
											y2: 1
									},
									stops: [
											[0, Highcharts.getOptions().colors[0]],
											[1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
									]
							},
							marker: {
									radius: 2
							},
							lineWidth: 1,
							states: {
									hover: {
											lineWidth: 1
									}
							},
							threshold: null
					}
			},

			series: [{
					type: 'area',
					name: 'Demand MWh',
					data: this.demand_chart_data
			}]
		});

		this.generation_chart = Highcharts.chart('generation-chart-container', {
			chart: {
				type: 'area',
				backgroundColor:this.chart_background_color,
			},
			title: {
				text: 'Generation (MW)',
				style: {
					color: this.chart_text_color
				}
			},
			subtitle: {
				text: ''
			},
			xAxis: {
				// categories: [],
				tickmarkPlacement: 'on',
				title: {
					enabled: false
				}
			},
			yAxis: {
				title: {
					text: 'MWh Dispatch'
				},
				labels: {
					
				}
			},
			tooltip: {
				split: true,
				
			},
			plotOptions: {
				area: {
					stacking: 'normal',
					lineColor: '#666666',
					lineWidth: 1,
					marker: {
						lineWidth: 1,
						lineColor: '#666666'
					}
				}
			},
			series: []
		});

		setInterval(function(){
			console.log('updating chart');
			// Get the last 500 data points so we dont crash the graphics engine
			var latest_spot_chart_data = app.spot_chart_data.slice(Math.max(app.spot_chart_data.length - 500, 1))
			var latest_demand_chart_data = app.demand_chart_data.slice(Math.max(app.demand_chart_data.length - 500, 1))
			// Chart the last 500 points
			app.spot_chart.series[0].setData(latest_spot_chart_data);
			app.demand_chart.series[0].setData(latest_demand_chart_data);
			
			// Generation Chart 
			var idx = 0;
			for(var gen in app.generation_chart_data){
				if(app.generation_chart.series.length<=idx){
					app.generation_chart.addSeries({name:gen, data:[]});
				}
				// Get the last 500 points so we dont crash the graphics engine
				var latest_generation_chart_data = app.generation_chart_data[gen].slice(Math.max(app.generation_chart_data[gen].length - 500, 1))
				// Chart the last 500 points
				app.generation_chart.series[idx].setData(latest_generation_chart_data)
				idx ++;
				console.log
			}
			// app.generation_chart.categories.setData(new Array(app.index))
		}, 1000);

	}

})






/**
 * Create a constructor for sparklines that takes some sensible defaults and merges in the individual
 * chart options. This function is also available from the jQuery plugin as $(element).highcharts('SparkLine').
 */
// Highcharts.SparkLine = function (a, b, c) {
//     var hasRenderToArg = typeof a === 'string' || a.nodeName,
//         options = arguments[hasRenderToArg ? 1 : 0],
//         defaultOptions = {
//             chart: {
//                 renderTo: (options.chart && options.chart.renderTo) || this,
//                 backgroundColor: null,
//                 borderWidth: 0,
//                 type: 'area',
//                 margin: [2, 0, 2, 0],
//                 width: 120,
//                 height: 20,
//                 style: {
//                     overflow: 'visible'
//                 },

//                 // small optimalization, saves 1-2 ms each sparkline
//                 skipClone: true
//             },
//             title: {
//                 text: ''
//             },
//             credits: {
//                 enabled: false
//             },
//             xAxis: {
//                 labels: {
//                     enabled: false
//                 },
//                 title: {
//                     text: null
//                 },
//                 startOnTick: false,
//                 endOnTick: false,
//                 tickPositions: []
//             },
//             yAxis: {
//                 endOnTick: false,
//                 startOnTick: false,
//                 labels: {
//                     enabled: false
//                 },
//                 title: {
//                     text: null
//                 },
//                 tickPositions: [0]
//             },
//             legend: {
//                 enabled: false
//             },
//             tooltip: {
//                 backgroundColor: null,
//                 borderWidth: 0,
//                 shadow: false,
//                 useHTML: true,
//                 hideDelay: 0,
//                 shared: true,
//                 padding: 0,
//                 positioner: function (w, h, point) {
//                     return { x: point.plotX - w / 2, y: point.plotY - h };
//                 }
//             },
//             plotOptions: {
//                 series: {
//                     animation: false,
//                     lineWidth: 1,
//                     shadow: false,
//                     states: {
//                         hover: {
//                             lineWidth: 1
//                         }
//                     },
//                     marker: {
//                         radius: 1,
//                         states: {
//                             hover: {
//                                 radius: 2
//                             }
//                         }
//                     },
//                     fillOpacity: 0.25
//                 },
//                 column: {
//                     negativeColor: '#910000',
//                     borderColor: 'silver'
//                 }
//             }
//         };

//     options = Highcharts.merge(defaultOptions, options);

//     return hasRenderToArg ?
//         new Highcharts.Chart(a, options, c) :
//         new Highcharts.Chart(options, b);
// };

// var start = +new Date(),
//     $tds = $('td[data-sparkline]'),
//     fullLen = $tds.length,
//     n = 0;

// // Creating 153 sparkline charts is quite fast in modern browsers, but IE8 and mobile
// // can take some seconds, so we split the input into chunks and apply them in timeouts
// // in order avoid locking up the browser process and allow interaction.
// function doChunk() {
//     var time = +new Date(),
//         i,
//         len = $tds.length,
//         $td,
//         stringdata,
//         arr,
//         data,
//         chart;

//     for (i = 0; i < len; i += 1) {
//         $td = $($tds[i]);
//         stringdata = $td.data('sparkline');
//         arr = stringdata.split('; ');
//         data = $.map(arr[0].split(', '), parseFloat);
//         chart = {};

//         if (arr[1]) {
//             chart.type = arr[1];
//         }
//         $td.highcharts('SparkLine', {
//             series: [{
//                 data: data,
//                 pointStart: 1
//             }],
//             tooltip: {
//                 headerFormat: '<span style="font-size: 10px">' + $td.parent().find('th').html() + ', Q{point.x}:</span><br/>',
//                 pointFormat: '<b>{point.y}.000</b> USD'
//             },
//             chart: chart
//         });

//         n += 1;

//         // If the process takes too much time, run a timeout to allow interaction with the browser
//         if (new Date() - time > 500) {
//             $tds.splice(0, i + 1);
//             setTimeout(doChunk, 0);
//             break;
//         }

//         // Print a feedback on the performance
//         if (n === fullLen) {
//             $('#result').html('Generated ' + fullLen + ' sparklines in ' + (new Date() - start) + ' ms');
//         }
//     }
// }
// doChunk();
