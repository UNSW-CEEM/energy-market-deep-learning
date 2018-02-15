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

var socket = io('http://localhost:5000');
socket.on('dispatched', function(data){console.log('dispatched',data)});
socket.on('connect', function(){console.log('connected')});
socket.on('nem_joined', function(data){console.log('nem_joined',data)});
socket.on('disconnect', function(){console.log('disconnected')});



console.log('listeners',socket.listeners('dispatched'))

// var app = new Vue({
// 	el: '#app',
// 	data: {
// 	  message: 'Hello Vue!',
// 	  dispatches:[{'hi':1},{'hi':2},{'hi':3}],
// 	},
// 	sockets:{
//     connect: function(){
// 			console.log('socket connected')
// 			this.$options.sockets.dispatched = (data) => {
// 				console.log(data)
// 			}
//     },
//     customEmit: function(val){
//       console.log('this method was fired by the socket server. eg: io.emit("customEmit", data)')
//     }
//   },

//   })