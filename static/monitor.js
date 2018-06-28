// Vue.use(VueWebsocket, "localhost:app.num_dps0");

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
// var connection = io.connect('ws://0.0.0.0:app.num_dps0');



// var socket = new eio.Socket('ws://localhost:app.num_dps0/');
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
		unmet_demand_chart_data:[],
		bid_scatter_chart_data:{},
		num_dps:500,
		
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

	methods:{
		update_bid_scatter(){
			// Bid Scatter Chart
			var idx = 1; //we start from 1 because 0 is the unmet demand.
			for(var gen in app.bid_scatter_chart_data){
				if(app.bid_scatter_chart.series.length<=idx){
					app.bid_scatter_chart.addSeries({name:gen, data:[], type:'scatter'});
				}
				// Get the last app.num_dps points so we dont crash the graphics engine
				var latest_bid_scatter_chart_data = app.bid_scatter_chart_data[gen].slice(Math.max(app.bid_scatter_chart_data[gen].length - app.num_dps, 1))
				// Chart the last app.num_dps points
				app.bid_scatter_chart.series[idx].setData(latest_bid_scatter_chart_data)
				idx ++;
			}
		}
	},
	

	mounted(){
		var socket = io('http://localhost:5000');
		socket.on('dispatched', function(market_state){
			// console.log('market_stateed',data)
			
			// console.log('updating chart')
			
			// app.spot_chart_data.push();
			app.spot_chart_data.push([app.index, market_state['price']]);
			app.demand_chart_data.push([app.index, market_state['demand']]);
			app.unmet_demand_chart_data.push([app.index, market_state['unmet_demand_MWh']]);
			// Add to generation chart data
			for(var gen in market_state['dispatch']){
				// If the generator is not in the charting data, put it in. 
				if(!(gen in app.generation_chart_data)){
					console.log('adding gen to gen chart data', gen);
					app.generation_chart_data[gen] = []
				}
				app.generation_chart_data[gen].push([app.index, market_state['dispatch'][gen]] )
			}

			//Add to bid chart data
			for(var gen in market_state['bids']){
				// If the generator is not in the charting data, put it in. 
				if(!(gen in app.bid_scatter_chart_data)){
					console.log('adding gen to gen chart data', gen);
					app.bid_scatter_chart_data[gen] = []
				}
				app.bid_scatter_chart_data[gen].push([market_state['bids'][gen].volume, market_state['bids'][gen].price] )
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

		this.bid_scatter_chart = Highcharts.chart('bid-scatter-chart-container', {
				chart: {
						zoomType: 'x',
						backgroundColor:this.chart_background_color,
				},
				title: {
						text: 'Bid Scatter',
						
						style: {
							color: this.chart_text_color
						}
				},
			subtitle: {
						text: document.ontouchstart === undefined ?
										'Click to Update Data. Click and drag in the plot area to zoom in' : 'Tap to Update Data. Pinch the chart to zoom in'
				},
				xAxis: {
						type: 'int',
						title:{
							text:'Volume (MWh)',
						}
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

				series: []
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
			},
			
		
		]
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
			// Get the last app.num_dps data points so we dont crash the graphics engine
			var latest_spot_chart_data = app.spot_chart_data.slice(Math.max(app.spot_chart_data.length - app.num_dps, 1))
			var latest_demand_chart_data = app.demand_chart_data.slice(Math.max(app.demand_chart_data.length - app.num_dps, 1))
			var latest_unmet_demand_chart_data = app.unmet_demand_chart_data.slice(Math.max(app.demand_chart_data.length - app.num_dps, 1))
			// Chart the last app.num_dps points
			app.spot_chart.series[0].setData(latest_spot_chart_data);
			app.demand_chart.series[0].setData(latest_demand_chart_data);
			
			
			// Generation Chart 
			// If the unmet demand series hasn't been appended, append it. 
			if(app.generation_chart.series.length == 0){
				app.generation_chart.addSeries({name:'Unmet Demand', data:[]});
			}
			app.generation_chart.series[0].setData(latest_unmet_demand_chart_data);
			var idx = 1; //we start from 1 because 0 is the unmet demand.
			for(var gen in app.generation_chart_data){
				if(app.generation_chart.series.length<=idx){
					app.generation_chart.addSeries({name:gen, data:[]});
				}
				// Get the last app.num_dps points so we dont crash the graphics engine
				var latest_generation_chart_data = app.generation_chart_data[gen].slice(Math.max(app.generation_chart_data[gen].length - app.num_dps, 1))
				// Chart the last app.num_dps points
				app.generation_chart.series[idx].setData(latest_generation_chart_data)
				idx ++;
			}

			// app.generation_chart.categories.setData(new Array(app.index))
		}, 1000);

	}

})




