import discord
import decouple
from discord.ext import commands
import mysql.connector

# Initialize the bot
Novabot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

# Establish connection to MySQL database
try:
    db = mysql.connector.connect(
        host=decouple.config("DB_HOST"),
        user=decouple.config("DB_USER"),
        password=decouple.config("DB_PASSWORD"),
        database=decouple.config("DB")
    )
    cursor = db.cursor()
except mysql.connector.Error as e:
    print(f"Error connecting to MySQL database: {e}")

# Global variable to keep track of whether the welcome message has been sent to the channel
welcome_message_sent = False

# Event handler for when a new member joins
@Novabot.event
async def on_member_join(member):
    global welcome_message_sent
    
    # Check if the welcome message has already been sent to the channel
    if not welcome_message_sent:
        try:
            # Send a welcome message to the channel with the embedded image
            channel = Novabot.get_channel(1236780018118692985)  # Replace with your channel ID
            if channel is not None:
                embed_channel = discord.Embed(
                    title="Welcome to the Server!",
                    description=f"Welcome {member.mention} to the server!\n\nWe're thrilled to have you join our community.\nOur community is friendly and diverse, so don't hesitate to join the conversation.\nIf you have any questions or need assistance, our moderators and members are here to help.\n\nEnjoy your time here and have fun!",
                    color=discord.Color.green()
                )
                # Add a GIF to the embedded message
                embed_channel.set_image(url="https://teeturtle.com/cdn/shop/files/TT-Im-Here-Youre-Welcome_4200x4200_SEPS.jpg?v=1703417379&width=1946")  # Replace with your GIF URL
                await channel.send(embed=embed_channel)
                welcome_message_sent = True
        except discord.DiscordException as e:
            print(f"Error sending welcome message: {e}")

    # Send a direct message to the new member
    try:
        embed_dm = discord.Embed(
            title="Welcome to the Server!",
            description="Welcome to the server! Enjoy your stay.",
            color=discord.Color.green()
        )
        # Add a GIF to the embedded message
        embed_dm.set_image(url="https://cdn.vectorstock.com/i/preview-1x/75/06/human-resources-welcoming-new-worker-concept-vector-38647506.webp")  # Replace with your GIF URL
        await member.send(embed=embed_dm)
    except discord.DiscordException as e:
        print(f"Error sending direct message to new member: {e}")

# Command to display top 10 most used words
@Novabot.command(name="word-status")
async def word_status(ctx):
    try:
        cursor.execute("SELECT word, COUNT(*) AS count FROM user_words GROUP BY word ORDER BY count DESC LIMIT 10")
        result = cursor.fetchall()
        response = "Top 10 most used words:\n"
        for row in result:
            response += f"{row[0]}: {row[1]}\n"
        await ctx.send(response)
    except mysql.connector.Error as e:
        await ctx.send(f"An error occurred while fetching word status: {e}")

# Command to display top 10 most used words by a specific user
@Novabot.command(name="user-status")
async def user_status(ctx, user: discord.Member):
    try:
        cursor.execute("SELECT word, COUNT(*) AS count FROM user_words WHERE discord_id = %s GROUP BY word ORDER BY count DESC LIMIT 10", (str(user.id),))
        result = cursor.fetchall()
        response = f"Top 10 most used words by {user.display_name}:\n"
        for row in result:
            response += f"{row[0]}: {row[1]}\n"
        await ctx.send(response)
    except mysql.connector.Error as e:
        await ctx.send(f"An error occurred while fetching user status: {e}")

# Command to select a role with buttons
@Novabot.command(name="select-role")
async def select_role(ctx):
    # Define available roles (replace with your actual roles)
    options = [
        "QA TESTER",
        "BACK-END DEVELOPER",
        "FRONT-END DEVELOPER",
        "UI DEVELOPER",
        "UI DESIGNER",
        "UX DESIGNER"
    ]
    
    try:
        # Create a message with buttons for selecting a role
        view = RoleSelectView(options)
        await ctx.send("Please select your role:", view=view)
    except discord.DiscordException as e:
        await ctx.send(f"An error occurred while creating role selection view: {e}")

# Custom class for role selection view
class RoleSelectView(discord.ui.View):
    def _init_(self, options):
        super()._init_()
        self.options = options
        for option in options:
            self.add_item(discord.ui.Button(label=option, style=discord.ButtonStyle.primary, custom_id=option))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

# Event handler to handle user selection of a role
@Novabot.event
async def on_interaction(interaction):
    if isinstance(interaction, discord.Interaction) and interaction.data.get('custom_id'):
        role = interaction.data['custom_id']
        try:
            # Update the user's role in the database
            cursor.execute("INSERT INTO user_role (discord_id, role) VALUES (%s, %s) ON DUPLICATE KEY UPDATE role = VALUES(role)", (str(interaction.user.id), role))
            db.commit()
            
            # Grant the selected role to the user on Discord
            guild = Novabot.get_guild(interaction.guild_id)
            user = guild.get_member(interaction.user.id)
            if user:
                selected_role = discord.utils.get(guild.roles, name=role)
                if selected_role:
                    await user.add_roles(selected_role)
                    await interaction.response.send_message(f"Role '{role}' has been assigned to {user.mention}.")
                else:
                    await interaction.response.send_message("Selected role not found.")
            else:
                await interaction.response.send_message("User not found.")
        except (discord.DiscordException, mysql.connector.Error) as e:
            print(f"An error occurred during role selection interaction: {e}")
            await interaction.response.send_message("An error occurred while processing your request. Please try again later.")

# Command error handler to handle unrecognized commands
@Novabot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Sorry, that command is not recognized.")

# Run the bot with the token
Novabot.run(decouple.config("TOKEN"))
