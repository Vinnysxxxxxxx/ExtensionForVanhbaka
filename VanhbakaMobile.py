import asyncio
import os
import discord
from discord.ext import commands
import json
import subprocess
import requests

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
auto_restart_task = None
process = None
auto_restart_enabled = False
auto_restart_minutes = 0
notification_enabled = True

# Abra o arquivo config.json
with open('config.json') as file:
    config = json.load(file)

allowed_user_ids = [int(x) for x in config["MISC"]["DISCORD_BOT"]["OWNER_USER_ID"]]
token = config["MISC"]["DISCORD_BOT"]["TOKEN"]

# Abra o arquivo notificacao.json
with open('notificação.json') as file:
    notification_data = json.load(file)
    webhook_url = notification_data["webhook_url"]
    notification_msg = notification_data["notification_msg"]

@bot.event
async def on_disconnect():
    if process:
        # Encerra o processo atual do arquivo main.py
        process.terminate()
        process.wait()

@bot.event
async def on_connect():
    # Inicia o processo do arquivo main.py quando o bot se conecta ao Discord
    start_process()

def start_process():
    global process
    process = subprocess.Popen(['python', 'main.py'])

def restart_process():
    global process
    if process:
        # Encerra o processo atual do arquivo main.py
        process.terminate()
        process.wait()
        process = None
    # Inicia um novo processo para executar o arquivo main.py
    start_process()

async def send_notification():
    if notification_enabled:
        embed = {
            "title": "Autorestart Notificação",
            "description": notification_msg,
            "color": 16737393  # Cor personalizada
        }
        payload = {
            "embeds": [embed]
        }
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao enviar a notificação via webhook: {e}")

async def auto_restart():
    global auto_restart_enabled
    global auto_restart_minutes

    while auto_restart_enabled:
        await asyncio.sleep(auto_restart_minutes * 60)
        restart_process()
        await send_notification()

@bot.command()
async def autorestart(ctx, minutes: int):
    global auto_restart_enabled
    if auto_restart_enabled:
        embed = discord.Embed(
            title="Erro",
            description="O reinício automático já está ativo. Use !autorestartoff para desativá-lo.",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        description="Você deseja receber notificação quando reiniciar? (sim/não)",
        color=discord.Colour.from_rgb(255, 0, 0)
    )
    await ctx.send(embed=embed)

    response = await bot.wait_for("message", check=lambda m: m.author == ctx.author)
    if response.content.lower() == "sim":
        notify_on_restart = True
        success_msg = "Notificação do webhook ativada."
    elif response.content.lower() == "não":
        notify_on_restart = False
        success_msg = "Notificação do webhook desativada."
    else:
        notify_on_restart = True  # Definir como padrão "sim" quando a resposta for inválida
        success_msg = "Resposta inválida. Notificação do webhook ativada por padrão."

    global auto_restart_task
    global auto_restart_minutes
    global notification_enabled

    embed = discord.Embed(
        title="Autorestart Ligado",
        color=discord.Colour.from_rgb(255, 0, 0)
    )
    embed.add_field(name="Status", value="A reinicialização automática foi habilitada.")
    embed.add_field(name="Minutes", value=f"Reiniciando a cada {minutes} minutos.")
    embed.add_field(name="Notificação", value=success_msg)
    await ctx.send(embed=embed)

    auto_restart_minutes = minutes
    auto_restart_enabled = True
    notification_enabled = notify_on_restart
    auto_restart_task = bot.loop.create_task(auto_restart())

@bot.command()
async def autorestartoff(ctx):
    # Verifica se o ID do usuário está na lista de IDs permitidos
    if ctx.author.id not in allowed_user_ids:
        embed = discord.Embed(
            title="Erro",
            description="Você não tem permissão para usar este comando.",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)
        return

    global auto_restart_task
    global auto_restart_enabled

    if not auto_restart_task:
        embed = discord.Embed(
            description="O reinício automático já está desativado.",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        description="Desativando o reinício automático...",
        color=discord.Colour.from_rgb(255, 0, 0)
    )
    await ctx.send(embed=embed)
    auto_restart_enabled = False
    auto_restart_task.cancel()
    auto_restart_task = None

    # Reinicia o processo
    restart_process()

@bot.command()
async def restart(ctx):
    # Verifica se o ID do usuário está na lista de IDs permitidos
    if ctx.author.id not in allowed_user_ids:
        embed = discord.Embed(
            title="Erro",
            description="Você não tem permissão para usar este comando.",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="Sucesso!",
        description="Reiniciou com sucesso o bot...",
        color=discord.Colour.from_rgb(255, 0, 0)
    )
    await ctx.send(embed=embed)
    restart_process()

@bot.command()
async def autorestartstats(ctx):
    # Verifica se o ID do usuário está na lista de IDs permitidos
    if ctx.author.id not in allowed_user_ids:
        embed = discord.Embed(
            title="Erro",
            description="Você não tem permissão para usar este comando.",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)
        return

    global auto_restart_enabled
    global auto_restart_minutes
    global notification_enabled

    if auto_restart_enabled:
        if notification_enabled:
            notification_status = "Ativada"
        else:
            notification_status = "Desativada"

        embed = discord.Embed(
            title="Autorestart Status",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        embed.add_field(name="Status", value="A reinicialização automática está ativada no momento.")
        embed.add_field(name="Minutes", value=f"Reiniciando a cada {auto_restart_minutes} minutos.")
        embed.add_field(name="Notificação", value=f"Notificação: {notification_status}")
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Stats Autorestart",
            description="O reinício automático está desativado.",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)

@bot.command()
async def support(ctx):
    embed = discord.Embed(
            title="Suporte",
            description="Para suporte entre em contato no Discord: elanaoteama",
            color=discord.Colour.from_rgb(255, 0, 0)
        )
    await ctx.send(embed=embed)

@bot.command()
async def comandos(ctx):
    commands_list = [
        "!autorestart <minutos>- Ativa o reinício automático a cada minuto escolhido.",
        "!autorestartoff - Desativa o reinício automático.",
        "!restart - Reinicia o arquivo o bot.",
        "!autorestartstats - Verifica o status do reinício automático.",
        "!stop - Encerra o bot (não faça isso sem motivo, só ira ligar manualmente)",
        "!support - Para obter suporte sobre o bot ou a extensão",
        "!comandos - Exibe a lista de comandos disponíveis."
        
    ]

    embed = discord.Embed(
        title="Comandos disponíveis",
        description="Lista de comandos disponíveis para uso:",
        color=discord.Colour.from_rgb(255, 0, 0)
    )
    for command in commands_list:
        embed.add_field(name="-----------------------------------------------------------------------------", value=command, inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def stop(ctx):
    # Verifica se o ID do usuário está na lista de IDs permitidos
    if ctx.author.id not in allowed_user_ids:
        embed = discord.Embed(
            title="Erro",
            description="Você não tem permissão para usar este comando.",
            color=discord.Color.from_rgb(255, 0, 0)
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title="Encerrando o bot",
        description="Encerrando o bot...",
        color=discord.Color.from_rgb(255, 0, 0)
    )
    await ctx.send(embed=embed)
    await bot.close()

bot.run(token)
