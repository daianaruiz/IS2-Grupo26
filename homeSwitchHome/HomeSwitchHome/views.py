from django.shortcuts import render, get_object_or_404, render_to_response
from .models import Propiedad, Semana, Subasta, Foto, Favorito, Postor, Perfil, Tarjeta, Reserva, Solicitud
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.views.generic.edit import FormView
from django.http.response import HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.urls import path
from django.urls import reverse_lazy
from django.shortcuts import redirect
from . import fechas
from .fechas import get_start_end_dates, monthdelta
from datetime import date, datetime, timedelta
from django.contrib.auth.views import LoginView, LogoutView
from HomeSwitchHome import forms
from django.forms import modelformset_factory
from django.template import RequestContext
from django.contrib import messages
from django.db import models
from django.core.mail import EmailMessage
import os
import random

# Create your views here.

def home(request):
	return render(request, 'HomeSwitchHome/home.html',{})

def listado_prop(request):
	propiedades = Propiedad.objects.all()
	template = 'HomeSwitchHome/listado_prop.html'
	return render(request, template, {'propiedades':propiedades})
	
def administracion(request):
		template = 'HomeSwitchHome/administracion.html'
		return render(request, template, {})

def ver_mis_reservas(request):
	l_res = Reserva.objects.filter(usuario_id=request.user.id)
	hoy = date.today() + timedelta(days=3)
	#l_sem = []
	#for r in l_res:
	#	l_sem.append(Semana.objects.get(reserva_id=r.id))
	return render(request,'HomeSwitchHome/ver_mis_reservas.html',{'l_res':l_res,'hoy':hoy})

def ver_mis_subastas(request):
	l_sub_id = Postor.objects.filter(usuario_id=request.user.id).order_by('subasta_id').distinct().values('subasta_id')
	l_sem = []
	for s in l_sub_id:
		l_sem.append(Semana.objects.get(subasta_id=s['subasta_id']))
	return render(request,'HomeSwitchHome/ver_mis_subastas.html',{'l_sem':l_sem})

def listado_res(request, id):
	p = Propiedad.objects.get(id=id)
	semanasR = Semana.objects.filter(reserva_id__isnull=False,propiedad_id=p.id)
	semanasD = Semana.objects.filter(habilitada_reserva=True,propiedad_id=p.id)
	return render(request, 'HomeSwitchHome/listado_res.html',{'semanasR':semanasR,'semanasD':semanasD,'prop':p})

def listado_prop_res(request):
	semanasR = Semana.objects.filter(reserva_id__isnull=False).order_by('propiedad_id').distinct()
	semanasD = Semana.objects.filter(habilitada_reserva=True).order_by('propiedad_id').distinct()
	propiedades = []
	for sem in semanasR:
		p = Propiedad.objects.get(id=sem.propiedad_id)
		propiedades.append(p)
	for sem in semanasD:
		p = Propiedad.objects.get(id=sem.propiedad_id)
		if p not in propiedades:
			propiedades.append(p)
	print(propiedades)
	return render(request, 'HomeSwitchHome/listado_prop_res.html',{'Propiedades':propiedades})

def propiedad(request, id):
	p = Propiedad.objects.get(id=id)
	res = Semana.objects.filter(propiedad_id=p.id, reserva_id__isnull=False).count()
	sub = Semana.objects.filter(propiedad_id=p.id, subasta_id__isnull=False).count()	
	semanas= Semana.objects.filter(propiedad_id=p.id)

	return render(request, 'HomeSwitchHome/propiedad.html',{'Propiedad':p,'res':res,'sub':sub,'semanas':semanas})

def ver_prop(request, id):
	p = Propiedad.objects.get(id=id)
	res = Semana.objects.filter(propiedad_id=p.id, reserva_id__isnull=False).count()
	sub = Semana.objects.filter(propiedad_id=p.id, subasta_id__isnull=False).count()	
	semanas= Semana.objects.filter(propiedad_id=p.id)
	es_premium = Perfil.objects.get(usuario=request.user).es_premium
	favs = Favorito.objects.filter(usuario_id=request.user).values('semana_id')
	sem_favs = []
	print(favs)
	for f in favs:
		sem_favs.append(Semana.objects.get(id=f['semana_id'])) 
	print(sem_favs)
	return render(request, 'HomeSwitchHome/ver_prop.html',{'user_favs':sem_favs,'Propiedad':p,'res':res,'sub':sub,'semanas':semanas,'es_premium':es_premium})

def agregar_fav(request, id):
	sem = Semana.objects.get(id=id)
	f = Favorito.objects.create(usuario_id=request.user.id,semana_id=sem.id)
	f.save()
	print('ADD FAV . . .'+str(f))
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def quitar_fav(request, id):
	sem = Semana.objects.get(id=id)
	f = Favorito.objects.get(usuario_id=request.user.id,semana_id=sem.id)
	print('REM FAV . . .'+str(f))
	f.delete()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	#return redirect(request.path)

def ver_fav(request):
	listado = Favorito.objects.filter(usuario_id=request.user.id).values('semana_id')
	semanas = []
	for s in listado:
		semanas.append(Semana.objects.get(id=s['semana_id']))
	return render(request, 'HomeSwitchHome/ver_fav.html',{'listado':semanas})

def realizar_reserva(request, id):
	semana = Semana.objects.get(id=id)
	r_hotsale = False
	tieneRes = Reserva.objects.filter(usuario_id=request.user,fecha_reserva=semana.fecha_inicio_sem).exists()
	tieneCred = Perfil.objects.get(usuario_id=request.user).creditos > 0
	print(tieneRes)
	print(tieneCred)
	return render(request, 'HomeSwitchHome/realizar_reserva.html',{'r_hotsale':r_hotsale,'semana':semana,'tieneRes':tieneRes,'tieneCred':tieneCred})

def realizar_reserva_hotsale(request, id):
	semana = Semana.objects.get(id=id)
	r_hotsale = True
	tieneRes = Reserva.objects.filter(usuario_id=request.user,fecha_reserva=semana.fecha_inicio_sem).exists()
	tieneCred = Perfil.objects.get(usuario_id=request.user).creditos > 0
	return render(request, 'HomeSwitchHome/realizar_reserva.html',{'r_hotsale':r_hotsale,'semana':semana,'tieneRes':tieneRes,'tieneCred':tieneCred})

def confirmar_reserva(request, id):
	semana = Semana.objects.get(id=id)
	perfil = Perfil.objects.get(usuario_id=request.user)
	r = Reserva.objects.create(usuario=request.user,reservada_desde='DIRECTA',fecha_reserva=semana.fecha_inicio_sem)
	perfil.creditos-=1
	perfil.save()
	semana.reserva_id = r.id
	semana.habilitada_reserva = False
	p= semana.propiedad.titulo
	mail=r.usuario.email
	email = EmailMessage('Reserva de propiedad ' + p, 'Se ha registrado una reserva a su nombre por la propiedad '+ p + ' para la semana ' + str(semana.fecha_inicio_sem), to=[mail])
	email.send()
	semana.save()
	r.save()

	messages.success(request,'Reserva realizada!')
	return redirect(reverse_lazy('home'))

def confirmar_reserva_hotsale(request, id):
	semana = Semana.objects.get(id=id)
	r = Reserva.objects.create(usuario=request.user,reservada_desde='HOTSALE',fecha_reserva=semana.fecha_inicio_sem)
	semana.reserva_id = r.id
	semana.habilitada_hotsale = False
	semana.save()
	r.save()
	messages.success(request,'Reserva Hot Sale realizada!')
	return redirect(reverse_lazy('home'))

def ver_cancelar_reserva(request, id):
	return render(request,'HomeSwitchHome/cancelar_reserva.html',{'id':id})
def cancelar_reserva(request, id):
	reserva = Reserva.objects.get(id=id)
	semana = Semana.objects.get(reserva_id=reserva.id)
	if date.today()+timedelta(days=3) < reserva.fecha_reserva:
		# MAS DE 6 M de anticipo
		p = Perfil.objects.get(usuario_id=semana.reserva.usuario.id)
		if semana.reserva.reservada_desde=='DIRECTA' or semana.reserva.reservada_desde=='SUBASTA':
			p.creditos+=1
		if fechas.mover_delta_meses(date.today(), 6) < reserva.fecha_reserva:
			semana.habilitada_reserva = True 
		else:
			semana.habilitada_reserva = False 
		semana.habilitada_subasta = False 
		semana.habilitada_hotsale = False 
		semana.reserva = None
		reserva.cancelada = True
		reserva.save()
		semana.save()
		messages.success(request,'Reserva Cancelada.')  	
	else:
		messages.error(request,'Periodo cancelacion excedido.')  	
	return redirect('home')

def eliminar_propiedad(request, id):
	p= Propiedad.objects.get(id=id)
	print('0------------')
	tieneRes = Semana.objects.filter(propiedad_id=p.id, reserva_id__isnull=False,fecha_inicio_sem__gt=date.today()).count()
	tieneSub = Semana.objects.filter(propiedad_id=p.id, subasta_id__isnull=False, fecha_inicio_sem__gt=date.today()).count()
	print(tieneRes)
	print(tieneSub)
	if tieneRes:
		print('1------')
		reservas= Semana.objects.filter(propiedad_id=p.id, reserva_id__isnull=False,fecha_inicio_sem__gt=date.today()).values('reserva_id')
		for r in reservas:
			reserva = Reserva.objects.get(id=r['reserva_id'])
			usuario = Perfil.objects.get(usuario_id=reserva.usuario_id)
			mail = User.objects.get(id=reserva.usuario_id).email
			email = EmailMessage('Propiedad eliminada ', 'La propiedad ' + p.titulo + ' se ha eliminado y su reserva para la semana ' + str(reserva.fecha_reserva) + ' fué cancelada.\nSe le reintegra la suma de 1 (uno) crédito', to=[mail])
			email.send()

			f=open(os.getcwd()+'/mail1', 'w')
			f.write('Asunto: Propiedad eliminada \nCuerpo: La propiedad ' + p.titulo + ' se ha eliminado y su reserva para la semana ' + str(reserva.fecha_reserva) + ' fué cancelada.\nSe le reintegra la suma de 1 (uno) crédito \n Para: ' + mail)
			messages.info(request, 'Se ha enviado un mail a '+mail+'(recupera +1 credito por Reserva Cancelada).')
			usuario.creditos+=1
			usuario.save()
			reserva.delete()
	elif tieneSub:
		for s in subastas:	
			subasta = Subasta.objects.delete(id=s['subasta'])
			usuario = Perfil.objects.get(usuario_id=s['usuario'])
			mail = User.objects.get(id=r['usuario']).mail
			email = EmailMessage('Propiedad eliminada ', 'La propiedad ' + p.titulo + ' se ha eliminado y la subasta para la semana ' + str(subasta.fecha_inicio_sem) + ' fué cancelada.', to=[mail])
			email.send()

			f=open(os.getcwd()+'/mail1', 'w')
			f.write('Asunto: Propiedad eliminada \nCuerpo: La propiedad ' + p.titulo + ' se ha eliminado y su reserva para la semana ' + str(subasta.fecha_inicio_sem) + ' fué cancelada.\nPara: ' + mail)
			messages.info(request, 'Se ha enviado mail a  '+mail+'(recupera +1 credito por Subasta Cerrada).')
			usuario.creditos+=1
			usuario.save()
	p.delete()
	messages.success(request, 'Propiedad eliminada.')
	return redirect(reverse_lazy(listado_prop))
	
def generar_semanas (request, id): 

	# La generacion de Semanas se realiza con un año de diferencia desde Hoy. 
	# Se generan las semanas restantes del año siguiente al actual,
	# y las semanas del año siguiente al año siguiente al actual. (En 2019: genera restantes del 2020 y todas del 2021). 
	# Se toma como actual al año siguiente de hoy(2019-> Actual es 2020) para mantener el delta de 12 meses exactos.

	p= Propiedad.objects.get(id=id)
	yy_actual = date.today().year  + 1
	existeActual=Semana.objects.filter(propiedad=p, fecha_inicio_sem__year=yy_actual).exists()
	existeActualSig=Semana.objects.filter(propiedad=p, fecha_inicio_sem__year=yy_actual+1).exists()

	if request.method == 'POST':
		año = int(request.POST.get('año'))


		if año == yy_actual and not existeActual:
			# GENERA SEMANAS RESTANTES 
			for i in range(date.today().isocalendar()[1],53):
				Semana.objects.create(propiedad= p, monto_base= 0, costo=0, numero_semana=i, fecha_inicio_sem=(get_start_end_dates(año, i))[0], fecha_fin_sem=(get_start_end_dates(año, i))[1])	
		elif año == (yy_actual + 1) and not existeActualSig:
			# GENERA TODAS LAS SEMANAS  
			for i in range(1,53):
				Semana.objects.create(propiedad= p, monto_base= 0, costo=0, numero_semana=i, fecha_inicio_sem=(get_start_end_dates(año, i))[0], fecha_fin_sem=(get_start_end_dates(año, i))[1])

		messages.success(request, "Semanas generadas!")
		return redirect(reverse_lazy('prop', kwargs= {'id':id}))
	else:
		return render(request, 'HomeSwitchHome/generar_semanas.html', {'existeActual':existeActual,'existeActualSig':existeActualSig,'actual':yy_actual, 'actualSig':yy_actual+1}) ### RENDER PARA BOTONES DE ELECCION DE AÑO ###

def listado_sem(request, id):
	listado= Semana.objects.filter(fecha_inicio_sem__gte= date.today()).filter(propiedad=id)
	############################################### GUARDAR SEMANA Y CREAR SUBASTA #########################################
	if request.method == 'POST':
		propiedad = Propiedad.objects.get(id=id)
		propiedad.subastas_activas+=1
		propiedad.save()
		nro = request.POST.get('semana')
		monto = request.POST.get('monto')
		print('NUMERO:   '+nro)
		print('MONTO:    '+monto)
		sem = listado.get(numero_semana= nro)
		print('SEMANA:  '+str(sem.numero_semana))
		print('SEMANA inicia:  '+str(sem.fecha_inicio_sem))
		print('SEMANA fin:  '+str(sem.fecha_fin_sem))
		sem.monto_base = monto
		sub = Subasta.objects.create(fecha_inicio = sem.fecha_inicio_sem,fecha_fin = sem.fecha_fin_sem)
		sem.subasta = sub
		sem.habilitada = False
		sem.save()
		return redirect(reverse_lazy('administracion')+'propiedad/'+id)
	else:
		return render(request, 'HomeSwitchHome/listado_sem.html', {'listado':listado})	

def habilitar_reservas(request, id):
	# SEMANAS QUE FALTEN ENTRE 12 MESES y 6 MESES PARA RESIDIR.
	# 
	listado = Semana.objects.filter(propiedad=id).filter(fecha_inicio_sem__lte= fechas.mover_delta_meses(date.today(), 12)).filter(fecha_inicio_sem__gt= fechas.mover_delta_meses(date.today(), 6),habilitada_reserva=False)
	if request.method == 'GET':
		p= Propiedad.objects.get(id=id)
		return render(request, 'HomeSwitchHome/habilitar_reservas.html', {'listado':listado,'p':id})
	else:
		seleccion = request.POST.get('semana')
		costo = request.POST.get('costo')
		semana = listado.get(numero_semana=seleccion)
		semana.costo = costo
		semana.habilitada_reserva = True
		semana.save()
		messages.success(request, "Se habilito la reserva !")
		return redirect(reverse_lazy('administracion'))

def habilitar_hotsales(request, id):
	# SEMANAS QUE FALTEN MENOS de 5 MESES y 27 dias PARA RESIDIR.
	# 
	listado = Semana.objects.filter(propiedad=id).filter(fecha_inicio_sem__lte= fechas.mover_delta_meses(date.today(), 5)+timedelta(days=27),habilitada_reserva=False,habilitada_subasta=False,habilitada_hotsale=False).filter(fecha_inicio_sem__gte= date.today())
	if request.method == 'GET':
		p= Propiedad.objects.get(id=id)
		return render(request, 'HomeSwitchHome/habilitar_hotsales.html', {'listado':listado,'p':id})
	else:
		seleccion = request.POST.get('semana')
		costo = request.POST.get('costo')
		semana = listado.get(numero_semana=seleccion)
		semana.costo = costo
		semana.habilitada_hotsale = True
		semana.habilitada_reserva = False
		semana.habilitada_subasta = False
		semana.save()
		messages.success(request, "Hot-Sale habilitado!")
		return redirect(reverse_lazy('administracion'))

def deshabilitar_hotsales(request, id):
	# SEMANAS QUE FALTEN MENOS de 5 MESES y 27 dias PARA RESIDIR.
	# 
	listado = Semana.objects.filter(propiedad=id).filter(fecha_inicio_sem__lt= fechas.mover_delta_meses(date.today(), 5)+timedelta(days=27),habilitada_reserva=False,habilitada_subasta=False,habilitada_hotsale=True)
	if request.method == 'GET':
		p= Propiedad.objects.get(id=id)
		return render(request, 'HomeSwitchHome/deshabilitar_hotsales.html', {'listado':listado})
	else:
		seleccion = request.POST.get('semana')
		semana = listado.get(numero_semana=seleccion)
		semana.habilitada_hotsale = False
		semana.save()
		messages.success(request, "Hot-Sale deshabilitado!")
		return redirect(reverse_lazy('administracion'))

def agregar_propiedad(request):
	Imageformset = modelformset_factory(Foto, form= forms.ImageForm ,min_num=0, max_num=5,extra=5)
	

	if request.method == 'GET':

		form = forms.PropiedadForm()
		formset = Imageformset(queryset=Foto.objects.none())
		#return render(request, 'HomeSwitchHome/agregar_propiedad.html', {'form':form, 'formset':formset})
	else:

		### POST ###

		form = forms.PropiedadForm(request.POST)
		formset = Imageformset(request.POST, request.FILES, queryset=Foto.objects.none())

		if form.is_valid() and formset.is_valid():
			print('Form OK')
			form = form.save(commit = False)
			form.save()
			file_list = [i for i in formset.cleaned_data if i]
			for f in file_list:
				archivo = f['archivo']
				foto = Foto(archivo=archivo, propiedad=form)
				foto.save()
			# for i in range(1,53):
			# 	Semana.objects.create(propiedad= form, monto_base= 0, costo=0, numero_semana=i, fecha_inicio_sem=(get_start_end_dates(2019, i))[0], fecha_fin_sem=(get_start_end_dates(2019, i))[1])
			messages.success(request, "Propiedad Agregada!")
			return redirect(reverse_lazy(administracion))

		else:
			print('Form Error')
	return render(request, 'HomeSwitchHome/agregar_propiedad.html', {'form':form, 'formset':formset})

def modificar_propiedad(request, id):
	Imageformset = modelformset_factory(Foto, form= forms.ImageForm ,min_num=0, max_num=5,extra=5)
	prop = get_object_or_404(Propiedad, id=id)
	if Semana.objects.filter(propiedad_id=prop.id, reserva_id__isnull=False).exists():
		form = forms.PropiedadConResForm(request.POST or None, instance=prop)
	else:
		form = forms.PropiedadForm(request.POST or None, instance=prop)

	fotos = Foto.objects.filter(propiedad=prop)
	formset = Imageformset(queryset=fotos)

	if request.method == 'POST':
		formset = Imageformset(request.POST,request.FILES, queryset=Foto.objects.filter(propiedad=prop))

		
		print('VALIDACION form:')
		print(form.is_valid())
		print('VALIDACION formset:')
		print(formset.is_valid())

		if form.is_valid() and formset.is_valid():
			print('Form OK!')
			
			form = form.save(commit = False)
			form.save()

			Foto.objects.filter(propiedad=prop).delete()
			
			#if hasattr(formset, 'deleted_objects'):
			#	for obj in formset.deleted_objects:
			#		obj.delete() 
			file_list = [i for i in formset.cleaned_data if i]
			print('FILELIST',file_list)
			for f in file_list:
			 	archivo = f['archivo']
			 	foto = Foto(archivo=archivo, propiedad=form)
			 	foto.save()

			messages.success(request, 'Propiedad modificada!')
			return redirect(reverse_lazy('administracion'))
		else:
			messages.success(request, 'La propiedad no se ha modificado.')
			return redirect(reverse_lazy('administracion'))
	return render(request, 'HomeSwitchHome/agregar_propiedad.html', {'form':form, 'formset':formset})

def borrar_fotos(request, id):
	prop = Propiedad.objects.get(id=id)
	fotos = Foto.objects.filter(propiedad=prop)
	for f in fotos:
		f.delete()
	messages.success(request,'Fotos eliminadas.')
	return redirect(reverse_lazy('modificar_prop',kwargs={'param': param}))

def abrir_subastas(request):
	ct=0
	ct2=0
	if request.method == 'POST':
		monto = request.POST.get('monto')	
		print()	
		semanas = Semana.objects.filter(reserva_id__isnull = True)
		for sem in semanas:

			fecha_desplazada = fechas.mover_delta_meses(sem.fecha_inicio_sem, -6)
			if (fecha_desplazada - timedelta(days=3)<= date.today() <= fecha_desplazada + timedelta(days=3) ) and not sem.habilitada_subasta:
				ct+=1
				ct2+=1
				propiedad = Propiedad.objects.get(id=sem.propiedad_id)
				propiedad.subastas_activas+=1
				prop = propiedad.titulo
				propiedad.save()
				sem.monto_base = monto
				sub = Subasta.objects.create(fecha_inicio = date.today(), fecha_inicio_sem=sem.fecha_inicio_sem)
				sem.subasta = sub
				sem.habilitada_reserva = False
				sem.habilitada_subasta = True
				fecha = sem.fecha_inicio_sem
				nro = sem.numero_semana
				sem.save()
				messages.success(request,prop+' Semana '+str(nro)+' ('+str(fecha)+') ahora está en subasta.')
		if ct == 0:
			messages.success(request,'No se abrieron subastas.')

		return redirect(reverse_lazy('administracion'))
	return render(request,'HomeSwitchHome/abrir_subastas.html',{})

def cerrar_subastas(request):
	ct=0
	subastas = Subasta.objects.all()
	for sub in subastas:
		delta = date.today()-sub.fecha_inicio
		print('DELTA: '+str(delta))
		sem = Semana.objects.get(subasta_id=sub.id)
		if delta.days >= 3:
			print('INGRESA a Cerrar ')
			print(sub)
			ct+=1
			hay_postores = Postor.objects.filter(subasta=sub).count()
			print(hay_postores)
			if not hay_postores:
				print('..NO Hay Postores..')
				messages.info(request,str(sem.propiedad.titulo)+' (SUB: '+str(sub.fecha_inicio_sem)+')'+'No se encontró ganador válido(No hay postores)')
			else:
				print('..Hay Postores..')
				ganador_valido = False
				while hay_postores and not ganador_valido:
					ultpostor = Postor.objects.filter(subasta=sub).latest('fecha_puja')
					ultpostor_perfil = Perfil.objects.get(usuario_id=ultpostor.usuario_id)
					tiene_reservas = Reserva.objects.filter(usuario_id=ultpostor.usuario_id, fecha_reserva=sub.fecha_inicio_sem).exists()
					if not tiene_reservas and ultpostor_perfil.creditos >= 1:
						messages.info(request,str(sem.propiedad.titulo)+'(SUB: '+str(sub.fecha_inicio_sem)+')'+'Se ha enviado un Mail al ganador '+ultpostor.usuario.email)
						ganador_valido = True
					else:
						if tiene_reservas:
							messages.info(request,str(sem.propiedad.titulo)+'(SUB: '+str(sub.fecha_inicio_sem)+')'+' El Postor '+ultpostor.usuario.email+' ya Tiene Reservas(No apto para ganar).')
						else:
							messages.info(request,str(sem.propiedad.titulo)+'(SUB: '+str(sub.fecha_inicio_sem)+')'+'El Postor '+ultpostor.usuario.email+' no tiene creditos(No apto para ganar).')
						ultpostor.delete()
						hay_postores = Postor.objects.filter(subasta=sub).count()
				if ganador_valido:
					sem = Semana.objects.get(subasta_id=sub.id)
					r = Reserva.objects.create(usuario_id=ultpostor.usuario_id,fecha_reserva=sub.fecha_inicio_sem,reservada_desde='SUBASTA')
					sem.reserva_id=r.id
					sem.habilitada_subasta=False
					titulo_prop = sem.propiedad.titulo
					mail = ultpostor.usuario.email
					email = EmailMessage('Finalización de subasta para propiedad ' + titulo_prop, '¡Ha ganado la subasta por la semana '+ str(sub.fecha_inicio_sem) + ' para la propiedad ' + titulo_prop +'!', to=[mail])
					email.send()
					sem.save()
					r.save()

				else:
					messages.info(request,'No se encontró ganador válido (Tienen creditos Insuficientes / Reservas Activas).')
			sub.delete()
	if ct:
		messages.success(request,'Se Cerraron '+str(ct)+' Subastas.')
	else:
		messages.info(request,'No hay subastas para cerrar.')

	return redirect(reverse_lazy('administracion'))

def buscar_x_fecha(request):
	##################### REVISAR FECHAS DEL POST ###############################

	if request.method == 'POST':
		fecha1= datetime.strptime(request.POST.get('f1'), '%Y-%m-%d').date()
		fecha2= datetime.strptime(request.POST.get('f2'), '%Y-%m-%d').date()
		if  (fecha2>fecha1) and (monthdelta(fecha1,fecha2) <= 2) and (monthdelta(date.today(),fecha1) >= 6 ) : 	
			listado_res = Semana.objects.filter(fecha_inicio_sem__range= (fecha1,fecha2)).select_related('propiedad')
			listado_prop = []
			for s in listado_res:
				p = Propiedad.objects.get(id=s.propiedad_id)
				if p not in listado_prop:
					listado_prop.append(p)

			if not request.user.is_authenticated:
				listado_prop = listado_prop[:5]
			return render (request, 'HomeSwitchHome/cuadrilla_prop.html',{'propiedades':listado_prop})
		else:

			if (fecha2<fecha1):

				messages.error(request, 'La fecha de fin del rango debe ser posterior a la fecha de inicio')
			elif (monthdelta(fecha1,fecha2) > 2):

				messages.error(request, 'El rango entre fechas no debe superar los dos meses')

			else:
				messages.error(request, 'La busqueda debe ser para al menos dentro de 6 meses')
			return render (request, 'HomeSwitchHome/buscar_x_fecha.html',{})
			#return render (request, 'HomeSwitchHome/',{}) ### ADVERTIR RANGO MAYOR A 2 MESES O BUSQUEDA MENOR A 6 MESES ###

	else:

		return render (request, 'HomeSwitchHome/buscar_x_fecha.html',{})

def buscar_x_zona (request):
	listado_zonas= Propiedad.objects.values('localidad').distinct()
	return render (request, 'HomeSwitchHome/buscar_x_zona.html',{'zonas':listado_zonas})

def  ver_cuadrilla_x_zona (request, zona):
	listado_res = Propiedad.objects.filter(localidad = zona)

	semanasR = Semana.objects.filter(habilitada_reserva=True).values('propiedad_id').distinct()
	semanasS = Semana.objects.filter(habilitada_subasta=True).values('propiedad_id').distinct()
	semanasH = Semana.objects.filter(habilitada_hotsale=True).values('propiedad_id').distinct()
	propR = []
	propS = []
	propH = []
	for s in semanasR:
		propR.append(Propiedad.objects.get(id=s['propiedad_id'],localidad = zona))
	for s in semanasS:
		propS.append(Propiedad.objects.get(id=s['propiedad_id'],localidad = zona))
	for s in semanasH:
		propH.append(Propiedad.objects.get(id=s['propiedad_id'],localidad = zona))

	if not request.user.is_authenticated:
				listado_res = listado_res[:5]
	return render (request, 'HomeSwitchHome/cuadrilla_prop.html',{'propiedades':listado_res,'propR':propR,'propS':propS,'propH':propH})

def ver_cuadrilla_propiedades(request):
	propiedades= Propiedad.objects.all()
	semanasR = Semana.objects.filter(habilitada_reserva=True).values('propiedad_id').distinct()
	semanasS = Semana.objects.filter(habilitada_subasta=True).values('propiedad_id').distinct()
	semanasH = Semana.objects.filter(habilitada_hotsale=True).values('propiedad_id').distinct()
	propR = []
	propS = []
	propH = []
	for s in semanasR:
		print('SEMANAS CON RESERVA')
		print(s['propiedad_id'])
		propR.append(Propiedad.objects.get(id=s['propiedad_id']))
	for s in semanasS:
		propS.append(Propiedad.objects.get(id=s['propiedad_id']))
	for s in semanasH:
		propH.append(Propiedad.objects.get(id=s['propiedad_id']))

	if not request.user.is_authenticated:
		propiedades = propiedades[:5]
	template = 'HomeSwitchHome/cuadrilla_prop.html'
	return render(request, template, {'propiedades':propiedades,'propR':propR,'propS':propS,'propH':propH})

def ver_subastas_activas(request):
	semanas= Semana.objects.exclude(subasta_id__isnull = True)
	template = 'HomeSwitchHome/subastas_activas.html'
	return render(request, template, {'semanas':semanas})

def recuperarClave(request):
	if request.method == 'POST':
		mail = request.POST.get('mail_usuario')
		#verificar mail exista. si existe,
		# enviar un mail con clave nueva.
		# sino informar que el mail es invalido.
		if User.objects.filter(email=mail):
			usuario=User.objects.get(email=mail)
			pas=''
			
			pas= ''.join(random.choice('0123456789ABCDEF') for _ in range(8))
			usuario.set_password(pas)
			usuario.save()
			print (pas)
			email = EmailMessage('Envío de nueva clave', 'Su nueva clave es '+ pas, to=[mail])
			email.send()
			messages.success(request,'Se ha enviado un mail con una nueva contraseña a ' + mail)
		else:
			messages.error(request,'El mail ingresado no existe en el sistema.')
		return redirect('InicioUser')
	else:
		return render(request, 'HomeSwitchHome/recuperar_clave.html', {})

def ingresar_subasta(request, id):

	subasta=Subasta.objects.get(id=id)
	semana = Semana.objects.get(subasta=subasta)
	args={}

	if request.method == 'POST':
		monto_puja = float(request.POST.get('monto_puja'))
		print('POST---')
		if request.user.perfil.creditos > 0:
			print('0-----------')
			if Postor.objects.filter(subasta_id=id).count() > 0:
				ultpostor = Postor.objects.filter(subasta=subasta).latest('fecha_puja')
				print('1-----------')
				if monto_puja > ultpostor.monto_puja and monto_puja>semana.monto_base:
					if not Reserva.objects.filter(usuario_id=request.user,fecha_reserva=semana.fecha_inicio_sem).exists():
						print('2--------')
						usuario_perfil = Perfil.objects.get(usuario=request.user)
						usuario_perfil.creditos-=1
						usuario_perfil.save()
						Postor.objects.create(usuario=request.user,subasta=subasta,monto_puja=monto_puja,fecha_puja=datetime.now())
						messages.success(request,'Puja de Subasta Registrada!')
					else:
						messages.error(request,'Ya tienes una Reserva en esa semana.')
				else:
					messages.error(request,'Monto de puja No Valido.')
			elif monto_puja>semana.monto_base:
				if not Reserva.objects.filter(usuario_id=request.user,fecha_reserva=semana.fecha_inicio_sem).exists():
					Postor.objects.create(usuario=request.user,subasta=subasta,monto_puja=monto_puja,fecha_puja=datetime.now())
					messages.success(request,'Puja de Subasta Registrada!')
				else:
					messages.error(request,'Ya tienes una Reserva en esa semana.')
			else:
				messages.error(request,'Monto de puja No Valido.')
		else:
			messages.error(request,'creditos insuficientes para participar en subasta.')
		return redirect(reverse_lazy('home'))
	else:
		if Postor.objects.filter(subasta_id=id).count() > 0:
			args={'semana':semana, 'monto_mas_alto':Postor.objects.filter(subasta_id=subasta).latest('fecha_puja').monto_puja}
		else:
			args={'semana':semana}
		return render(request, 'HomeSwitchHome/ingresar_subasta.html', args)

def RegistroUsuario(request):
	if request.method == 'POST':
		user_form = forms.UserForm(request.POST, prefix="user_form")
		perfil_form = forms.PerfilForm(request.POST, prefix="perfil_form")
		tarj_form = forms.TarjetaForm(request.POST, prefix="tarj_form")
		print('-------------')
		print(user_form.is_valid())
		print(perfil_form.is_valid())
		print(tarj_form.is_valid())
		print('-------------')
		if user_form.is_valid() and perfil_form.is_valid() and tarj_form.is_valid():
			u = user_form.save(commit= False)
			p = perfil_form.save(commit=False)
			t = tarj_form.save(commit=False)
			u.username = u.email
			u.is_staff = False
			u.is_superuser = False
			u.save()
			u = User.objects.get(username=u.email)
			p.usuario_id = u.id
			t.usuario_id = u.id 
			p.save()
			t.save()
			password = user_form.cleaned_data.get('password1')
			usuario = authenticate(username=u, password=password)
			login(request, usuario)
			messages.success(request, 'Perfil Creado con exito!')
			return redirect('home')
		else:
			return render(request, 'HomeSwitchHome/user_auth.html', {
			'user_form': user_form,
			'perfil_form': perfil_form,
			'tarj_form': tarj_form
			})

			#messages.error(request, 'Datos Incorrectos.')
			#return redirect('RegistroUser')
	else:
		user_form = forms.UserForm(prefix="user_form")
		perfil_form = forms.PerfilForm(prefix="perfil_form")
		tarj_form = forms.TarjetaForm(prefix="tarj_form")
		return render(request, 'HomeSwitchHome/user_auth.html', {
		'user_form': user_form,
		'perfil_form': perfil_form,
		'tarj_form': tarj_form})

class RegistroAdmin (CreateView):
	model= User
	template_name= "HomeSwitchHome/admin_auth.html"
	form_class = UserCreationForm
	success_url=reverse_lazy('administracion')

	def form_valid(self, form):
		u = form.save(commit=False)
		u.is_staff = True
		u.is_superuser = True
		u.save()
		usuario = form.cleaned_data.get('username')
		password = form.cleaned_data.get('password1')
		usuario = authenticate(username=usuario, password=password)
		login(self.request, usuario)
		return redirect(reverse_lazy('administracion'))

def userLogin(request):
	if request.method == 'POST': 
		form = AuthenticationForm(request.POST)
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				# Redirect to a successpage
				return redirect(reverse_lazy('home'))
			else:
				messages.error(request, 'Cuenta deshabilitada.')
		else:
			messages.error(request, 'Mail o contraseña Incorrecta.')
	else:
		form = AuthenticationForm()
	return render(request,"HomeSwitchHome/iniciar_sesion.html",{'form':form})

def userLogout(request):
	logout(request)
	return redirect(reverse_lazy('home'))

class Login (LoginView):
	template_name = 'HomeSwitchHome/admin_auth.html'
class Logout(LogoutView):
	pass

def listado_usuarios(request):
	perfiles=Perfil.objects.all()
	return render(request, 'HomeSwitchHome/listado_usuarios.html', {'perfiles': perfiles})

def ver_perfil_usuario(request, id):
	print(request.user.id)
	perfil = Perfil.objects.get(usuario=id)
	return render(request, 'HomeSwitchHome/perfil_usuario.html', {'perfil':perfil})

def verPerfil(request):
	if request.method=='POST':
		tipo = request.POST.get('tipo')
		motivo = request.POST.get('motivo')
		Solicitud.objects.create(usuario=request.user,tipo=tipo,motivo=motivo)
		messages.success(request,'Solicitud de'+ tipo +' Premium enviada.')
		return redirect('home')
	else:	
		print(request.user.id)
		perfil = Perfil.objects.get(usuario=request.user.id)
		tarjeta = Tarjeta.objects.get(usuario=request.user.id)
		solicitud_alta = None
		solicitud_baja = None
		if Solicitud.objects.filter(usuario_id=request.user.id,tipo='BAJA').count():
			solicitud_baja = Solicitud.objects.get(usuario_id=request.user.id,tipo='BAJA')
		if Solicitud.objects.filter(usuario_id=request.user.id,tipo='ALTA').count():
			solicitud_alta = Solicitud.objects.get(usuario_id=request.user.id,tipo='ALTA')
		return render(request, 'HomeSwitchHome/mi_perfil.html', {'usuario': request.user,'perfil':perfil,'tarjeta':tarjeta,'solicitud_baja':solicitud_baja,'solicitud_alta':solicitud_alta})

def solicitar_baja(request):
	if request.method=='POST':
		motivo = request.POST.get('motivo')
		Solicitud.objects.create(usuario=request.user,tipo='BAJA',motivo=motivo)
		messages.success(request,'Solicitud de Baja Premium enviada.')
		return redirect('home')

def solicitar_alta(request):
	if request.method=='POST':
		motivo = request.POST.get('motivo')
		Solicitud.objects.create(usuario=request.user,tipo='ALTA',motivo=motivo)
		messages.success(request,'Solicitud de Alta Premium enviada.')
	return redirect('home')

def aceptar_baja(request, id):
	solicitud = Solicitud.objects.get(id=id)
	perfil = Perfil.objects.get(usuario_id=solicitud.usuario_id)
	perfil.es_premium = False
	perfil.save()
	solicitud.delete()
	messages.success(request,'Solicitud de Baja Premium Aceptada.')
	return redirect('ver_solicitudes')

def rechazar_baja(request, id):
	solicitud = Solicitud.objects.get(id=id)
	solicitud.delete()
	messages.success(request,'Solicitud de Baja Premium Rechazada.')
	return redirect('ver_solicitudes')

def aceptar_alta(request, id):
	solicitud = Solicitud.objects.get(id=id)
	perfil = Perfil.objects.get(usuario_id=solicitud.usuario_id)
	perfil.es_premium = True
	perfil.save()
	solicitud.delete()
	messages.success(request,'Solicitud de Alta Premium Aceptada.')
	return redirect('ver_solicitudes')

def rechazar_alta(request, id):
	solicitud = Solicitud.objects.get(id=id)
	solicitud.delete()
	messages.success(request,'Solicitud de Alta Premium Rechazada.')
	return redirect('ver_solicitudes')

def ver_solicitudes(request):
	solicitudes = Solicitud.objects.all()
	return render(request, 'HomeSwitchHome/ver_solicitudes.html',{'solicitudes':solicitudes})

def editarPerfil(request, id):
	user = User.objects.get(id=id)
	perfil = Perfil.objects.get(usuario=id)
	tarjeta = Tarjeta.objects.get(usuario=id)
	user_form = forms.UserForm(request.POST or None, instance=user, prefix="user_form")
	perfil_form = forms.PerfilForm(request.POST or None, instance=perfil, prefix="perfil_form")
	tarj_form = forms.TarjetaForm(request.POST or None, instance=tarjeta, prefix="tarj_form")
	#mail = user_form.cleaned_data.get('email')
	if request.method == 'POST':
		if user_form.is_valid() and perfil_form.is_valid() and tarj_form.is_valid():
			messages.success(request,'Perfil Actualizado Correctamente.')
			user_form.save()
			perfil_form.save()
			tarj_form.save()
			usuario = user_form.cleaned_data.get('email')
			password = user_form.cleaned_data.get('password1')
			usuario = authenticate(username=usuario, password=password)
			login(request, usuario)
			return redirect('home')
	#		elif not user_form.is_valid():
	#			user_form['password'].validate()
	#			if mail == user_form.cleaned_data.get('email'):

	return render(request, 'HomeSwitchHome/editar_perfil.html',{'usuario':user_form,'perfil':perfil_form,'tarjeta':tarj_form})

