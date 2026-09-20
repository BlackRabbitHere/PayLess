package com.paymentoptimizer;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import org.junit.jupiter.api.Test;
import org.springframework.web.bind.annotation.RestController;

class ArchitectureTest {
    @Test
    void moduleBoundariesRemainIntact() throws Exception {
        // Use the application's output location so custom build directories cannot accidentally include test classes.
        var classes = new ClassFileImporter().importPath(java.nio.file.Path.of(
                PaymentOptimizerApplication.class.getProtectionDomain().getCodeSource().getLocation().toURI()));
        noClasses().that().resideOutsideOfPackage("..integration.scraper..")
                .should().dependOnClassesThat().resideInAnyPackage("..integration.scraper..").check(classes);
        noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat()
                .resideInAnyPackage("org.springframework..", "..integration..", "..controller..", "..persistence..", "..dto..").check(classes);
        noClasses().that().areAnnotatedWith(RestController.class).should().dependOnClassesThat()
                .resideInAnyPackage("..integration..", "..persistence..", "org.springframework.web.client..").check(classes);
        noClasses().that().resideOutsideOfPackage("..persistence..").should().dependOnClassesThat()
                .resideInAnyPackage("jakarta.persistence..", "java.sql..", "org.springframework.data..").check(classes);
        noClasses().that().resideInAPackage("..application..").should().dependOnClassesThat()
                .resideInAnyPackage("..persistence..").check(classes);
        noClasses().that().resideInAPackage("..integration.scraper.client..")
                .and().haveSimpleName("ScraperClient").should().dependOnClassesThat()
                .resideInAnyPackage("..query..", "..offers..", "..optimization..", "..wallet..", "..mapper..").check(classes);
        noClasses().that().resideInAPackage("..query..")
                .should().dependOnClassesThat().resideInAnyPackage("..integration..", "org.springframework.web.client..").check(classes);
        noClasses().that().haveSimpleName("OptimizationController").should().dependOnClassesThat()
                .haveNameMatching(".*(CostCalculator|RouteGenerator|PaymentRouteOptimizer|QueryUnderstandingService|OfferAcquisitionService|ScraperClient)")
                .check(classes);
        noClasses().that().resideInAPackage("..optimization..")
                .and().doNotHaveSimpleName("CostCalculator").should().callMethod(java.math.BigDecimal.class, "add", java.math.BigDecimal.class).check(classes);
        noClasses().that().resideInAPackage("..optimization..")
                .and().doNotHaveSimpleName("CostCalculator").should().callMethod(java.math.BigDecimal.class, "subtract", java.math.BigDecimal.class).check(classes);
        noClasses().that().resideInAPackage("..optimization..")
                .and().doNotHaveSimpleName("CostCalculator").should().callMethod(java.math.BigDecimal.class, "multiply", java.math.BigDecimal.class).check(classes);
    }
}
