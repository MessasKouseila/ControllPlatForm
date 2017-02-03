//console.log("coucou")
var bouton = document.getElementsByClassName('deco')
for (var i = 0; i < bouton.length; i++) {

	console.log(this.bouton[i])
	this.bouton[i].addEventListener('click', function (event) {
						var reponse = window.confirm("vous voulez vous deconnecter ?")
						if (!reponse) {
							event.stopPropagation()
							event.preventDefault()
						}
						})
}
var listes = document.querySelectorAll('il')
for (var i = 0; i < listes.length; i++) {
	console.log(listes[i].innerText)
}