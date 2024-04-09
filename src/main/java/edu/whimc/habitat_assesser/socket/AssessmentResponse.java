package edu.whimc.habitat_assesser.socket;

public class AssessmentResponse {

    private String user;
    private int id;
    private String lowestCategory;
    private String highestCategory;
    private int area;
    private int communicationsFacilities;
    private int food;
    private int gravity;
    private int health;
    private int oxygenRegulation;
    private int powerGeneration;
    private int radiationProtection;
    private int supplies;
    private int shape;
    private int transportation;
    public AssessmentResponse () {
        super();
    }

    public AssessmentResponse(int id, String user, String lowestCategory, String highestCategory, int area, int communicationsFacilities, int food,
                              int gravity, int health, int oxygenRegulation, int powerGeneration, int radiationProtection, int supplies, int shape,
                              int transportation) {
        this.id = id;
        this.user = user;
        this.lowestCategory = lowestCategory;
        this.highestCategory = highestCategory;
        this.area = area;
        this.communicationsFacilities = communicationsFacilities;
        this.food = food;
        this.gravity = gravity;
        this.health = health;
        this.oxygenRegulation = oxygenRegulation;
        this.powerGeneration = powerGeneration;
        this.radiationProtection = radiationProtection;
        this.supplies = supplies;
        this.shape = shape;
        this.transportation = transportation;
    }


    public String getUser() {
        return user;
    }

    public int getId() {
        return id;
    }

    public String getLowestCategory(){return lowestCategory;}
    public String getHighestCategory(){return highestCategory;}
    public int getArea() {
        return area;
    }
    public int getCommunicationsFacilities() {
        return communicationsFacilities;
    }
    public int getFood() {
        return food;
    }
    public int getHealth() {
        return health;
    }
    public int getGravity() {
        return gravity;
    }
    public int getOxygenRegulation() {
        return oxygenRegulation;
    }
    public int getPowerGeneration() {
        return powerGeneration;
    }
    public int getRadiationProtection() {
        return radiationProtection;
    }
    public int getSupplies() {
        return supplies;
    }
    public int getShape() {
        return shape;
    }
    public int getTransportation() {
        return transportation;
    }

    public String toString(){
        return "ID" + this.getId() + "\n" +
                "Name" + this.getUser() + "\n" +
                "lowestCategory" + this.getLowestCategory() + "\n" +
                "highestCategory" + this.getHighestCategory() + "\n" +
                "area" + this.getArea() + "\n" +
                "communications" + this.getCommunicationsFacilities() + "\n" +
                "food" + this.getFood() + "\n" +
                "gravity" + this.getGravity() + "\n" +
                "health" + this.getHealth() + "\n" +
                "oxygen" + this.getOxygenRegulation() + "\n" +
                "power" + this.getPowerGeneration() + "\n" +
                "radiation" + this.getRadiationProtection() + "\n" +
                "supplies" +this.getSupplies() + "\n" +
                "shape" + this.getShape() + "\n" +
                "transportation" + this.getTransportation();
    }
}