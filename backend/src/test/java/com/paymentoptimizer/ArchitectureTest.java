package com.paymentoptimizer;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.Test;
import org.springframework.web.bind.annotation.RestController;

class ArchitectureTest {
    @Test
    void moduleBoundariesRemainIntact() {
        var classes = new ClassFileImporter().withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("com.paymentoptimizer");
        noClasses().that().resideOutsideOfPackage("..integration.scraper..")
                .should().dependOnClassesThat().resideInAnyPackage("..integration.scraper..").check(classes);
        noClasses().that().resideInAPackage("..domain..").should().dependOnClassesThat()
                .resideInAnyPackage("org.springframework..", "..integration..", "..controller..", "..persistence..", "..dto..").check(classes);
        noClasses().that().areAnnotatedWith(RestController.class).should().dependOnClassesThat()
                .resideInAnyPackage("..integration..", "..persistence..", "org.springframework.web.client..").check(classes);
        noClasses().should().dependOnClassesThat().resideInAnyPackage("jakarta.persistence..", "java.sql..").check(classes);
        noClasses().that().resideInAPackage("..integration.scraper.client..")
                .and().haveSimpleName("ScraperClient").should().dependOnClassesThat()
                .resideInAnyPackage("..query..", "..offers..", "..optimization..", "..wallet..", "..mapper..").check(classes);
        noClasses().that().resideInAPackage("..query..")
                .should().dependOnClassesThat().resideInAnyPackage("..integration..", "org.springframework.web.client..").check(classes);
    }
}
