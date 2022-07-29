package edu.whimc.photographer;

import com.corundumstudio.socketio.SocketIOClient;
import com.gmail.filoghost.holographicdisplays.api.HologramsAPI;
import edu.whimc.observations.models.Observation;
import edu.whimc.observations.models.ObserveEvent;
import java.util.Collection;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import javax.annotation.Nullable;
import org.bukkit.Bukkit;
import org.bukkit.ChatColor;
import org.bukkit.GameMode;
import org.bukkit.Location;
import org.bukkit.entity.Player;

public class CameraOperator {

    private static final Set<CameraOperator> operators = new HashSet<>();

    private final Photographer plugin;
    private final UUID playerUuid;
    private final UUID clientUuid;

    /** Previous things about the player */
    private GameMode prevGameMode;
    private Location prevLocation;

    private @Nullable ObserveEvent currentEvent = null;

    private CameraOperator(Photographer plugin, Player player, SocketIOClient client) {
        this.plugin = plugin;
        this.playerUuid = player.getUniqueId();
        this.clientUuid = client.get("uuid");
    }

    public static Optional<CameraOperator> registerCameraOperator(Photographer plugin, Player player, SocketIOClient client) {
        if (getCameraOperator(player.getUniqueId()).isPresent()
                || getCameraOperator(client.get("uuid")).isPresent()) {
            return Optional.empty();
        }

        CameraOperator operator = new CameraOperator(plugin, player, client);

        // Save player state
        operator.prevLocation = player.getLocation();
        operator.prevGameMode = player.getGameMode();

        // Prepare the player for being a camera operator
        player.setGameMode(GameMode.SPECTATOR);

        // Hide all players
        Bukkit.getOnlinePlayers().forEach(p -> player.hidePlayer(plugin, p));

        // Hide all holograms from the player
        HologramsAPI.getHolograms(plugin.getObservationsPlugin()).forEach(hologram ->
                hologram.getVisibilityManager().hideTo(player));

        CameraOperator.operators.add(operator);
        return Optional.of(operator);
    }

    public void unregister() {
        Player player = getPlayer();
        player.sendMessage(ChatColor.GOLD + "" + ChatColor.GOLD + "You are no longer a photographer");
        CameraOperator.operators.remove(this);

        Bukkit.getScheduler().runTask(this.plugin, () -> {
            // Restore the state of the player
            player.teleport(this.prevLocation);
            player.setGameMode(this.prevGameMode);

            // Show all players
            Bukkit.getOnlinePlayers().forEach(p -> player.showPlayer(this.plugin, p));

            // Show all holograms
            HologramsAPI.getHolograms(plugin.getObservationsPlugin()).forEach(hologram ->
                    hologram.getVisibilityManager().resetVisibility(player));
        });
    }

    public static Optional<CameraOperator> getAvailableOperator() {
        return CameraOperator.operators.stream()
                .filter(CameraOperator::isAvailable)
                .findFirst();
    }

    public static Collection<CameraOperator> getAllCameraOperators() {
        return CameraOperator.operators;
    }

    public static Optional<CameraOperator> getCameraOperator(UUID playerOrSocketUuid) {
        for (CameraOperator operator : CameraOperator.operators) {
            if (operator.playerUuid.equals(playerOrSocketUuid)
                    || operator.clientUuid.equals(playerOrSocketUuid)) {
                return Optional.of(operator);
            }
        }
        return Optional.empty();
    }

    public void photograph(ObserveEvent event) {
        this.currentEvent = event;
        Player player = getPlayer();
        player.sendMessage(ChatColor.YELLOW + event.getPlayer().getName() + " made an observation. " +
                "Teleporting to view location for photograph.");

        Observation observation = event.getObservation();

        // Make the observation invisible
        observation.getHologram().getVisibilityManager().hideTo(player);
        player.teleport(observation.getViewLocation());

        String strippedObservation = ChatColor.stripColor(observation.getObservation());

        Bukkit.getScheduler().runTaskAsynchronously(this.plugin, () ->
                getClient().sendEvent("screenshot", observation.getId(), strippedObservation)
        );
    }

    public Player getPlayer() {
        return Bukkit.getPlayer(this.playerUuid);
    }

    public boolean isAvailable() {
        return this.currentEvent == null;
    }

    public UUID getPlayerUuid() {
        return this.playerUuid;
    }

    public UUID getClientUuid() {
        return this.clientUuid;
    }

    public @Nullable ObserveEvent getCurrentEvent() {
        return this.currentEvent;
    }

    public void setCurrentEvent(@Nullable ObserveEvent event) {
        this.currentEvent = event;
    }

    public SocketIOClient getClient() {
        // This should never be null
        return this.plugin.getClient(this.clientUuid).get();
    }

}
